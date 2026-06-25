from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies import require_role
from app.models import Enrollment, Homework, HomeworkSubmission, User, UserRole
from app.routers.files import build_download_url
from app.schemas import (
    GradeIn,
    HomeworkIn,
    HomeworkOut,
    HomeworkSubmissionOut,
    LeaderboardItem,
    StudentHomeworkOut,
    SubmissionIn,
    TutorHomeworkOut,
)

router = APIRouter(prefix="/homework", tags=["homework"])

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".svg", ".avif"}


def _is_image_file(file_name: str | None) -> bool:
    if not file_name:
        return False
    return Path(file_name).suffix.lower() in IMAGE_EXTENSIONS


def _file_url(file_key: str | None, file_name: str | None) -> str | None:
    if not file_key:
        return None
    is_image = _is_image_file(file_name)
    return build_download_url(file_key, None if is_image else file_name)


def _submission_out(submission: HomeworkSubmission, student_name: str) -> HomeworkSubmissionOut:
    return HomeworkSubmissionOut(
        id=submission.id,
        student_id=submission.student_id,
        student_name=student_name,
        file_name=submission.file_name,
        file_url=_file_url(submission.file_key, submission.file_name),
        is_image=_is_image_file(submission.file_name),
        grade=submission.grade,
        teacher_comment=submission.teacher_comment,
        created_at=submission.created_at,
    )


def _homework_out(homework: Homework, target_student_name: str | None = None) -> HomeworkOut:
    return HomeworkOut(
        id=homework.id,
        title=homework.title,
        description=homework.description,
        target_student_id=homework.target_student_id,
        target_student_name=target_student_name,
        attachment_file_name=homework.attachment_file_name,
        attachment_file_url=_file_url(homework.attachment_file_key, homework.attachment_file_name),
        is_image=_is_image_file(homework.attachment_file_name),
        created_at=homework.created_at,
    )


@router.post("", response_model=HomeworkOut)
def create_homework(
    payload: HomeworkIn,
    tutor: User = Depends(require_role(UserRole.tutor)),
    db: Session = Depends(get_db),
):
    if payload.target_student_id is not None:
        enrollment = (
            db.query(Enrollment)
            .filter(Enrollment.tutor_id == tutor.id, Enrollment.student_id == payload.target_student_id)
            .first()
        )
        if not enrollment:
            raise HTTPException(status_code=404, detail="Ученик не найден в вашем списке")

    homework = Homework(
        tutor_id=tutor.id,
        target_student_id=payload.target_student_id,
        title=payload.title,
        description=payload.description,
        attachment_file_key=payload.attachment_file_key,
        attachment_file_name=payload.attachment_file_name,
    )
    db.add(homework)
    db.commit()
    db.refresh(homework)
    target_student_name = None
    if homework.target_student_id:
        target_student = db.get(User, homework.target_student_id)
        target_student_name = target_student.full_name if target_student else None
    return _homework_out(homework, target_student_name)


@router.get("", response_model=list[StudentHomeworkOut])
def list_homework(user: User = Depends(require_role(UserRole.student)), db: Session = Depends(get_db)):
    rows = (
        db.query(Homework, User, HomeworkSubmission)
        .join(Enrollment, Enrollment.tutor_id == Homework.tutor_id)
        .join(User, User.id == Homework.tutor_id)
        .outerjoin(
            HomeworkSubmission,
            (HomeworkSubmission.homework_id == Homework.id) & (HomeworkSubmission.student_id == user.id),
        )
        .filter(
            Enrollment.student_id == user.id,
            (Homework.target_student_id.is_(None)) | (Homework.target_student_id == user.id),
        )
        .order_by(Homework.created_at.desc(), Homework.id.desc())
        .all()
    )
    return [
        StudentHomeworkOut(
            **_homework_out(homework, user.full_name if homework.target_student_id == user.id else None).model_dump(),
            tutor_id=tutor.id,
            tutor_name=tutor.full_name,
            submission=_submission_out(submission, user.full_name) if submission else None,
        )
        for homework, tutor, submission in rows
    ]


@router.get("/my", response_model=list[TutorHomeworkOut])
def list_my_homework(user: User = Depends(require_role(UserRole.tutor)), db: Session = Depends(get_db)):
    homeworks = (
        db.query(Homework, User.full_name)
        .outerjoin(User, User.id == Homework.target_student_id)
        .filter(Homework.tutor_id == user.id)
        .order_by(Homework.created_at.desc(), Homework.id.desc())
        .all()
    )

    items: list[TutorHomeworkOut] = []
    for homework, target_student_name in homeworks:
        submissions = (
            db.query(HomeworkSubmission, User.full_name)
            .join(User, User.id == HomeworkSubmission.student_id)
            .filter(HomeworkSubmission.homework_id == homework.id)
            .order_by(HomeworkSubmission.created_at.desc(), HomeworkSubmission.id.desc())
            .all()
        )
        items.append(
            TutorHomeworkOut(
                **_homework_out(homework, target_student_name).model_dump(),
                submissions=[_submission_out(submission, student_name) for submission, student_name in submissions],
            )
        )
    return items


@router.post("/submissions")
def submit_homework(
    payload: SubmissionIn,
    student: User = Depends(require_role(UserRole.student)),
    db: Session = Depends(get_db),
):
    homework = db.get(Homework, payload.homework_id)
    if not homework:
        raise HTTPException(status_code=404, detail="Задание не найдено")
    enrolled = db.query(Enrollment).filter_by(student_id=student.id, tutor_id=homework.tutor_id).first()
    if not enrolled:
        raise HTTPException(status_code=403, detail="Вы не прикреплены к этому учителю")
    if homework.target_student_id is not None and homework.target_student_id != student.id:
        raise HTTPException(status_code=403, detail="Это задание назначено другому ученику")

    submission = db.query(HomeworkSubmission).filter_by(homework_id=payload.homework_id, student_id=student.id).first()
    if not submission:
        submission = HomeworkSubmission(
            homework_id=payload.homework_id,
            student_id=student.id,
            file_key=payload.file_key,
            file_name=payload.file_name,
        )
        db.add(submission)
    else:
        submission.file_key = payload.file_key
        submission.file_name = payload.file_name
        submission.grade = None
        submission.teacher_comment = None
    db.commit()
    db.refresh(submission)
    return _submission_out(submission, student.full_name)


@router.patch("/submissions/{submission_id}/grade")
def grade_submission(
    submission_id: int,
    payload: GradeIn,
    tutor: User = Depends(require_role(UserRole.tutor)),
    db: Session = Depends(get_db),
):
    submission = db.get(HomeworkSubmission, submission_id)
    if not submission:
        raise HTTPException(status_code=404, detail="Ответ не найден")
    homework = db.get(Homework, submission.homework_id)
    if homework.tutor_id != tutor.id:
        raise HTTPException(status_code=403, detail="Это не ваше задание")
    submission.grade = payload.grade
    submission.teacher_comment = (payload.teacher_comment or "").strip() or None
    db.commit()
    return {"status": "graded"}


@router.get("/leaderboard", response_model=list[LeaderboardItem])
def leaderboard(db: Session = Depends(get_db)):
    rows = (
        db.query(
            User.id,
            User.full_name,
            func.avg(HomeworkSubmission.grade).label("average_grade"),
            func.count(HomeworkSubmission.grade).label("graded_count"),
        )
        .join(HomeworkSubmission, HomeworkSubmission.student_id == User.id)
        .filter(HomeworkSubmission.grade.is_not(None))
        .group_by(User.id)
        .order_by(func.avg(HomeworkSubmission.grade).desc(), func.count(HomeworkSubmission.grade).desc())
        .limit(20)
        .all()
    )
    return [
        LeaderboardItem(
            student_id=row.id,
            full_name=row.full_name,
            average_grade=round(float(row.average_grade), 2),
            graded_count=row.graded_count,
        )
        for row in rows
    ]
