from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies import get_current_user, require_role
from app.models import (
    ApprovalStatus,
    Chat,
    ChatMessage,
    Enrollment,
    Subject,
    TutorOfferPackage,
    TutorProfile,
    TutorReview,
    User,
    UserRole,
)
from app.routers.files import build_download_url
from app.schemas import (
    NextLessonUpdateIn,
    ReviewOut,
    TutorCardOut,
    TutorOfferPackageIn,
    TutorOfferPackageOut,
    TutorOfferIn,
    TutorOfferOut,
    TutorProfileOut,
    TutorProfileUpdateIn,
    TutorReviewIn,
    TutorStudentOut,
)

router = APIRouter(prefix="/tutors", tags=["tutors"])


def _avatar_url(user: User | None) -> str | None:
    if not user or not user.avatar_file_key:
        return None
    return build_download_url(user.avatar_file_key)


def _packages_for_tutor(tutor_id: int, db: Session) -> list[TutorOfferPackageOut]:
    packages = (
        db.query(TutorOfferPackage)
        .filter(TutorOfferPackage.tutor_id == tutor_id, TutorOfferPackage.is_active.is_(True))
        .order_by(TutorOfferPackage.created_at.desc(), TutorOfferPackage.id.desc())
        .all()
    )
    return [TutorOfferPackageOut.model_validate(package) for package in packages]


def _reviews_for_tutor(tutor_id: int, db: Session) -> list[ReviewOut]:
    rows = (
        db.query(TutorReview, User)
        .join(User, User.id == TutorReview.student_id)
        .filter(TutorReview.tutor_id == tutor_id)
        .order_by(TutorReview.created_at.desc())
        .all()
    )
    return [
        ReviewOut(
            id=review.id,
            student_id=student.id,
            student_name=student.full_name,
            stars=review.stars,
            text=review.text,
            created_at=review.created_at,
            student_avatar_url=_avatar_url(student),
        )
        for review, student in rows
    ]


def _can_student_review(student: User | None, tutor_id: int, db: Session) -> bool:
    if not student or student.role != UserRole.student:
        return False
    return (
        db.query(Enrollment)
        .filter(Enrollment.student_id == student.id, Enrollment.tutor_id == tutor_id)
        .first()
        is not None
    )


def _is_student_enrolled(student: User | None, tutor_id: int, db: Session) -> bool:
    if not student or student.role != UserRole.student:
        return False
    return (
        db.query(Enrollment)
        .filter(Enrollment.student_id == student.id, Enrollment.tutor_id == tutor_id)
        .first()
        is not None
    )


def _default_next_lesson() -> datetime:
    base = datetime.utcnow() + timedelta(days=3)
    return base.replace(hour=18, minute=0, second=0, microsecond=0)


@router.get("", response_model=list[TutorCardOut])
def list_tutors(
    subject: Subject | None = None,
    current_user: User | None = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rating_subquery = (
        db.query(
            TutorReview.tutor_id.label("tutor_id"),
            func.avg(TutorReview.stars).label("average_rating"),
            func.count(TutorReview.id).label("review_count"),
        )
        .group_by(TutorReview.tutor_id)
        .subquery()
    )

    query = (
        db.query(User, TutorProfile, rating_subquery.c.average_rating, rating_subquery.c.review_count)
        .join(TutorProfile, TutorProfile.user_id == User.id)
        .outerjoin(rating_subquery, rating_subquery.c.tutor_id == User.id)
        .filter(
            User.role == UserRole.tutor,
            User.approval_status == ApprovalStatus.approved,
            TutorProfile.offer_published.is_(True),
        )
    )
    if subject:
        query = query.filter(TutorProfile.subject == subject)

    return [
        TutorCardOut(
            id=user.id,
            full_name=user.full_name,
            avatar_url=_avatar_url(user),
            subject=profile.subject,
            price_rub=profile.price_rub,
            description=profile.description or "",
            average_rating=round(float(average_rating or 0), 2),
            review_count=int(review_count or 0),
            is_enrolled=_is_student_enrolled(current_user, user.id, db),
            offer_count=1 + len(_packages_for_tutor(user.id, db)),
        )
        for user, profile, average_rating, review_count in query.order_by(User.full_name).all()
        if profile.subject is not None and profile.price_rub is not None
    ]


@router.get("/{tutor_id}", response_model=TutorProfileOut)
def tutor_profile(
    tutor_id: int,
    current_user: User | None = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    tutor = db.get(User, tutor_id)
    if not tutor or tutor.role != UserRole.tutor or tutor.approval_status != ApprovalStatus.approved:
        raise HTTPException(status_code=404, detail="Репетитор не найден")

    profile = db.query(TutorProfile).filter(TutorProfile.user_id == tutor.id).first()
    if not profile or not profile.offer_published:
        raise HTTPException(status_code=404, detail="Профиль репетитора еще не опубликован")

    average_rating, review_count = (
        db.query(func.avg(TutorReview.stars), func.count(TutorReview.id))
        .filter(TutorReview.tutor_id == tutor.id)
        .one()
    )

    return TutorProfileOut(
        id=tutor.id,
        full_name=tutor.full_name,
        avatar_url=_avatar_url(tutor),
        subject=profile.subject,
        price_rub=profile.price_rub,
        description=profile.description or "",
        bio=profile.bio or "",
        education=profile.education or "",
        experience=profile.experience or "",
        lesson_format=profile.lesson_format or "",
        average_rating=round(float(average_rating or 0), 2),
        review_count=int(review_count or 0),
        is_enrolled=_is_student_enrolled(current_user, tutor.id, db),
        can_review=_can_student_review(current_user, tutor.id, db),
        reviews=_reviews_for_tutor(tutor.id, db),
        packages=_packages_for_tutor(tutor.id, db),
    )


@router.post("/{tutor_id}/reviews")
def save_review(
    tutor_id: int,
    payload: TutorReviewIn,
    student: User = Depends(require_role(UserRole.student)),
    db: Session = Depends(get_db),
):
    tutor = db.get(User, tutor_id)
    if not tutor or tutor.role != UserRole.tutor or tutor.approval_status != ApprovalStatus.approved:
        raise HTTPException(status_code=404, detail="Репетитор не найден")
    if not _can_student_review(student, tutor_id, db):
        raise HTTPException(status_code=403, detail="Оставить отзыв можно только после занятий с репетитором")

    review = db.query(TutorReview).filter_by(student_id=student.id, tutor_id=tutor_id).first()
    if not review:
        review = TutorReview(student_id=student.id, tutor_id=tutor_id, stars=payload.stars, text=payload.text)
        db.add(review)
    else:
        review.stars = payload.stars
        review.text = payload.text
    db.commit()
    return {"status": "ok", "message": "Отзыв сохранен"}


@router.put("/me/offer")
def save_offer(
    payload: TutorOfferIn,
    tutor: User = Depends(require_role(UserRole.tutor)),
    db: Session = Depends(get_db),
):
    profile = db.query(TutorProfile).filter(TutorProfile.user_id == tutor.id).first()
    if not profile:
        profile = TutorProfile(user_id=tutor.id)
        db.add(profile)
    profile.subject = payload.subject
    profile.price_rub = payload.price_rub
    profile.description = payload.description
    if not profile.bio:
        profile.bio = payload.description
    profile.offer_published = payload.offer_published
    db.commit()
    return {"status": "ok", "message": "Предложение успешно создано"}


@router.get("/me/offer", response_model=TutorOfferOut)
def get_offer(
    tutor: User = Depends(require_role(UserRole.tutor)),
    db: Session = Depends(get_db),
):
    profile = db.query(TutorProfile).filter(TutorProfile.user_id == tutor.id).first()
    if not profile:
        return TutorOfferOut()
    return TutorOfferOut(
        subject=profile.subject,
        price_rub=profile.price_rub,
        description=profile.description or "",
        bio=profile.bio or "",
        education=profile.education or "",
        experience=profile.experience or "",
        lesson_format=profile.lesson_format or "",
        offer_published=profile.offer_published,
        packages=_packages_for_tutor(tutor.id, db),
    )


@router.post("/me/offers", response_model=TutorOfferPackageOut)
def create_offer_package(
    payload: TutorOfferPackageIn,
    tutor: User = Depends(require_role(UserRole.tutor)),
    db: Session = Depends(get_db),
):
    package = TutorOfferPackage(
        tutor_id=tutor.id,
        title=payload.title,
        subject=payload.subject,
        price_rub=payload.price_rub,
        description=payload.description,
        is_active=True,
    )
    db.add(package)
    db.commit()
    db.refresh(package)
    return TutorOfferPackageOut.model_validate(package)


@router.delete("/me/offers/{offer_id}")
def delete_offer_package(
    offer_id: int,
    tutor: User = Depends(require_role(UserRole.tutor)),
    db: Session = Depends(get_db),
):
    package = (
        db.query(TutorOfferPackage)
        .filter(TutorOfferPackage.id == offer_id, TutorOfferPackage.tutor_id == tutor.id)
        .first()
    )
    if not package:
        raise HTTPException(status_code=404, detail="Предложение не найдено")

    package.is_active = False
    db.commit()
    return {"status": "deleted", "message": "Предложение удалено"}


@router.get("/me/students", response_model=list[TutorStudentOut])
def list_my_students(
    tutor: User = Depends(require_role(UserRole.tutor)),
    db: Session = Depends(get_db),
):
    enrollments = (
        db.query(Enrollment, User)
        .join(User, User.id == Enrollment.student_id)
        .filter(Enrollment.tutor_id == tutor.id)
        .order_by(Enrollment.created_at.desc(), User.full_name.asc())
        .all()
    )

    changed = False
    result: list[TutorStudentOut] = []
    for enrollment, student in enrollments:
        if enrollment.next_lesson_at is None:
            enrollment.next_lesson_at = _default_next_lesson()
            changed = True
        result.append(
            TutorStudentOut(
                student_id=student.id,
                full_name=student.full_name,
                email=student.email,
                avatar_url=_avatar_url(student),
                enrolled_at=enrollment.created_at,
                next_lesson_at=enrollment.next_lesson_at,
            )
        )

    if changed:
        db.commit()

    return result


@router.patch("/me/students/{student_id}")
def update_my_student_lesson(
    student_id: int,
    payload: NextLessonUpdateIn,
    tutor: User = Depends(require_role(UserRole.tutor)),
    db: Session = Depends(get_db),
):
    enrollment = (
        db.query(Enrollment)
        .filter(Enrollment.tutor_id == tutor.id, Enrollment.student_id == student_id)
        .first()
    )
    if not enrollment:
        raise HTTPException(status_code=404, detail="Ученик не найден")

    enrollment.next_lesson_at = payload.next_lesson_at
    db.commit()
    return {"status": "ok", "message": "Следующее занятие обновлено"}


@router.patch("/me/profile")
def update_my_profile(
    payload: TutorProfileUpdateIn,
    tutor: User = Depends(require_role(UserRole.tutor)),
    db: Session = Depends(get_db),
):
    profile = db.query(TutorProfile).filter(TutorProfile.user_id == tutor.id).first()
    if not profile:
        profile = TutorProfile(user_id=tutor.id)
        db.add(profile)
    profile.bio = payload.bio
    profile.education = payload.education
    profile.experience = payload.experience
    profile.lesson_format = payload.lesson_format
    db.commit()
    return {"status": "ok", "message": "Личный кабинет обновлен"}


@router.post("/{tutor_id}/enroll")
def enroll_to_tutor(
    tutor_id: int,
    student: User = Depends(require_role(UserRole.student)),
    db: Session = Depends(get_db),
):
    tutor = db.get(User, tutor_id)
    if not tutor or tutor.role != UserRole.tutor or tutor.approval_status != ApprovalStatus.approved:
        raise HTTPException(status_code=404, detail="Репетитор не найден")
    existing = db.query(Enrollment).filter_by(student_id=student.id, tutor_id=tutor_id).first()
    if existing:
        return {"status": "already_enrolled"}
    db.add(Enrollment(student_id=student.id, tutor_id=tutor_id, next_lesson_at=_default_next_lesson()))
    existing_chat = db.query(Chat).filter_by(student_id=student.id, tutor_id=tutor_id).first()
    if not existing_chat:
        db.add(Chat(student_id=student.id, tutor_id=tutor_id))
    db.commit()
    return {"status": "enrolled"}


@router.delete("/{tutor_id}/enroll")
def unenroll_from_tutor(
    tutor_id: int,
    student: User = Depends(require_role(UserRole.student)),
    db: Session = Depends(get_db),
):
    tutor = db.get(User, tutor_id)
    if not tutor or tutor.role != UserRole.tutor or tutor.approval_status != ApprovalStatus.approved:
        raise HTTPException(status_code=404, detail="Репетитор не найден")

    enrollment = db.query(Enrollment).filter_by(student_id=student.id, tutor_id=tutor_id).first()
    if not enrollment:
        return {"status": "not_enrolled"}

    chat = db.query(Chat).filter_by(student_id=student.id, tutor_id=tutor_id).first()
    if chat:
        db.query(ChatMessage).filter(ChatMessage.chat_id == chat.id).delete()
        db.delete(chat)

    db.delete(enrollment)
    db.commit()
    return {"status": "unenrolled"}
