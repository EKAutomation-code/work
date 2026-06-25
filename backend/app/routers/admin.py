from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies import require_admin
from app.models import (
    ApprovalStatus,
    Chat,
    ChatMessage,
    Enrollment,
    Homework,
    HomeworkSubmission,
    TutorOfferPackage,
    TutorProfile,
    TutorReview,
    User,
    UserRole,
    Webinar,
)
from app.schemas import AdminApprovalIn, UserOut

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users", response_model=list[UserOut])
def list_users(_: dict = Depends(require_admin), db: Session = Depends(get_db)):
    return db.query(User).order_by(User.created_at.desc()).all()


@router.patch("/users/{user_id}/approval", response_model=UserOut)
def update_approval(
    user_id: int,
    payload: AdminApprovalIn,
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    if user.role == UserRole.tutor and payload.status == ApprovalStatus.approved and not payload.kyc_verified:
        raise HTTPException(status_code=400, detail="Репетитору нужен KYC перед одобрением")

    user.approval_status = payload.status
    if payload.kyc_verified is not None:
        user.kyc_verified = payload.kyc_verified
    db.commit()
    db.refresh(user)
    return user


@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    if user.role == UserRole.admin:
        raise HTTPException(status_code=400, detail="Аккаунт администратора удалять нельзя")

    if user.role == UserRole.tutor:
        homework_ids = [homework_id for (homework_id,) in db.query(Homework.id).filter(Homework.tutor_id == user.id).all()]
        if homework_ids:
            db.query(HomeworkSubmission).filter(HomeworkSubmission.homework_id.in_(homework_ids)).delete(
                synchronize_session=False
            )
            db.query(Homework).filter(Homework.id.in_(homework_ids)).delete(synchronize_session=False)

        chat_ids = [chat_id for (chat_id,) in db.query(Chat.id).filter(Chat.tutor_id == user.id).all()]
        if chat_ids:
            db.query(ChatMessage).filter(ChatMessage.chat_id.in_(chat_ids)).delete(synchronize_session=False)
            db.query(Chat).filter(Chat.id.in_(chat_ids)).delete(synchronize_session=False)

        db.query(Enrollment).filter(Enrollment.tutor_id == user.id).delete(synchronize_session=False)
        db.query(TutorOfferPackage).filter(TutorOfferPackage.tutor_id == user.id).delete(synchronize_session=False)
        db.query(TutorReview).filter(TutorReview.tutor_id == user.id).delete(synchronize_session=False)
        db.query(Webinar).filter(Webinar.tutor_id == user.id).delete(synchronize_session=False)
        db.query(TutorProfile).filter(TutorProfile.user_id == user.id).delete(synchronize_session=False)
    else:
        student_chat_ids = [chat_id for (chat_id,) in db.query(Chat.id).filter(Chat.student_id == user.id).all()]
        if student_chat_ids:
            db.query(ChatMessage).filter(ChatMessage.chat_id.in_(student_chat_ids)).delete(synchronize_session=False)
            db.query(Chat).filter(Chat.id.in_(student_chat_ids)).delete(synchronize_session=False)

        db.query(HomeworkSubmission).filter(HomeworkSubmission.student_id == user.id).delete(synchronize_session=False)
        db.query(Enrollment).filter(Enrollment.student_id == user.id).delete(synchronize_session=False)
        db.query(TutorReview).filter(TutorReview.student_id == user.id).delete(synchronize_session=False)

    db.delete(user)
    db.commit()
    return {"status": "deleted"}
