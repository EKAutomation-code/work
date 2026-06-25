from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies import require_approved
from app.models import Chat, ChatMessage, Enrollment, TutorProfile, User, UserRole
from app.routers.files import build_download_url
from app.schemas import ChatMessageIn, ChatMessageOut, ChatSummaryOut

router = APIRouter(prefix="/chats", tags=["chats"])


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".svg", ".avif"}


def _is_image_file(file_name: str | None) -> bool:
    if not file_name:
        return False
    return Path(file_name).suffix.lower() in IMAGE_EXTENSIONS


def _avatar_url(user: User | None) -> str | None:
    if not user or not user.avatar_file_key:
        return None
    return build_download_url(user.avatar_file_key)


def _message_out(message: ChatMessage, sender: User) -> ChatMessageOut:
    is_image = _is_image_file(message.file_name)
    file_url = build_download_url(message.file_key, None if is_image else message.file_name) if message.file_key else None
    return ChatMessageOut(
        id=message.id,
        sender_id=message.sender_id,
        sender_name=sender.full_name,
        sender_avatar_url=_avatar_url(sender),
        text=message.text,
        file_key=message.file_key,
        file_name=message.file_name,
        file_url=file_url,
        is_image=is_image,
        created_at=message.created_at,
    )


def _find_chat_for_user(chat_id: int, user: User, db: Session) -> Chat:
    chat = db.get(Chat, chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Чат не найден")
    if user.id not in {chat.student_id, chat.tutor_id}:
        raise HTTPException(status_code=403, detail="Нет доступа к этому чату")
    return chat


@router.get("", response_model=list[ChatSummaryOut])
def list_chats(user: User = Depends(require_approved), db: Session = Depends(get_db)):
    if user.role == UserRole.student:
        chats = db.query(Chat).filter(Chat.student_id == user.id).order_by(Chat.created_at.desc()).all()
        partner_role = UserRole.tutor
    elif user.role == UserRole.tutor:
        chats = db.query(Chat).filter(Chat.tutor_id == user.id).order_by(Chat.created_at.desc()).all()
        partner_role = UserRole.student
    else:
        return []

    result = []
    for chat in chats:
        partner_id = chat.tutor_id if user.role == UserRole.student else chat.student_id
        partner = db.get(User, partner_id)
        profile = db.query(TutorProfile).filter(TutorProfile.user_id == chat.tutor_id).first()
        last_message = (
            db.query(ChatMessage)
            .filter(ChatMessage.chat_id == chat.id)
            .order_by(ChatMessage.created_at.desc(), ChatMessage.id.desc())
            .first()
        )
        result.append(
            ChatSummaryOut(
                id=chat.id,
                partner_id=partner_id,
                partner_name=partner.full_name if partner else "Собеседник",
                partner_avatar_url=_avatar_url(partner),
                partner_role=partner_role,
                subject=profile.subject if profile else None,
                price_rub=profile.price_rub if profile else None,
                last_message_text=last_message.text if last_message else None,
                last_message_file_name=last_message.file_name if last_message else None,
                last_message_at=last_message.created_at if last_message else chat.created_at,
            )
        )
    return result


@router.get("/{chat_id}/messages", response_model=list[ChatMessageOut])
def list_messages(
    chat_id: int,
    user: User = Depends(require_approved),
    db: Session = Depends(get_db),
):
    _find_chat_for_user(chat_id, user, db)
    messages = (
        db.query(ChatMessage, User)
        .join(User, User.id == ChatMessage.sender_id)
        .filter(ChatMessage.chat_id == chat_id)
        .order_by(ChatMessage.created_at.asc(), ChatMessage.id.asc())
        .all()
    )
    return [
        _message_out(message, sender)
        for message, sender in messages
    ]


@router.post("/{chat_id}/messages", response_model=ChatMessageOut)
def send_message(
    chat_id: int,
    payload: ChatMessageIn,
    user: User = Depends(require_approved),
    db: Session = Depends(get_db),
):
    chat = _find_chat_for_user(chat_id, user, db)
    if not (payload.text and payload.text.strip()) and not payload.file_key:
        raise HTTPException(status_code=400, detail="Добавьте текст или вложение")

    enrolled = (
        db.query(Enrollment)
        .filter(Enrollment.student_id == chat.student_id, Enrollment.tutor_id == chat.tutor_id)
        .first()
    )
    if not enrolled:
        raise HTTPException(status_code=403, detail="Чат доступен только после прикрепления ученика к учителю")

    message = ChatMessage(
        chat_id=chat.id,
        sender_id=user.id,
        text=(payload.text or "").strip() or None,
        file_key=payload.file_key,
        file_name=payload.file_name,
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return _message_out(message, user)
