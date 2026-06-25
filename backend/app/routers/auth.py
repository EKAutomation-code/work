from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password, make_email_code, verify_password
from app.db.session import get_db
from app.dependencies import get_current_user, verify_admin_credentials
from app.routers.files import build_download_url
from app.models import ApprovalStatus, TutorProfile, User, UserRole
from app.schemas import CurrentUserOut, EmailCodeIn, LoginIn, ProfileUpdateIn, RegisterIn, TokenOut, UserOut, VerifyEmailIn

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/me", response_model=CurrentUserOut)
def me(user: User = Depends(get_current_user)):
    return CurrentUserOut(
        id=user.id,
        role=user.role,
        token_role=user.role,
        email=user.email,
        full_name=user.full_name,
        about=user.about,
        avatar_url=build_download_url(user.avatar_file_key) if user.avatar_file_key else None,
        approval_status=user.approval_status,
        email_verified=user.email_verified,
        kyc_verified=user.kyc_verified,
    )


@router.patch("/me", response_model=CurrentUserOut)
def update_me(
    payload: ProfileUpdateIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if payload.full_name is not None:
        user.full_name = payload.full_name.strip()
    if payload.about is not None:
        user.about = payload.about.strip() or None
    if payload.avatar_file_key is not None:
        user.avatar_file_key = payload.avatar_file_key
    db.commit()
    db.refresh(user)
    return CurrentUserOut(
        id=user.id,
        role=user.role,
        token_role=user.role,
        email=user.email,
        full_name=user.full_name,
        about=user.about,
        avatar_url=build_download_url(user.avatar_file_key) if user.avatar_file_key else None,
        approval_status=user.approval_status,
        email_verified=user.email_verified,
        kyc_verified=user.kyc_verified,
    )


@router.post("/register", response_model=UserOut)
def register(payload: RegisterIn, db: Session = Depends(get_db)):
    if payload.role == UserRole.admin:
        raise HTTPException(status_code=400, detail="Админ создается через переменные окружения")
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=409, detail="Email уже занят")

    user = User(
        role=payload.role,
        email=payload.email,
        full_name=payload.full_name,
        password_hash=hash_password(payload.password),
        email_code=make_email_code(),
        approval_status=ApprovalStatus.pending,
    )
    db.add(user)
    db.flush()
    if payload.role == UserRole.tutor:
        db.add(TutorProfile(user_id=user.id))
    db.commit()
    db.refresh(user)

    # TODO: подключить SMTP/почтовый сервис. На dev код возвращается в логах API.
    print(f"Email code for {user.email}: {user.email_code}")
    return user


@router.post("/verify-email", response_model=UserOut)
def verify_email(payload: VerifyEmailIn, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or user.email_code != payload.code:
        raise HTTPException(status_code=400, detail="Неверный код")
    user.email_verified = True
    user.email_code = None
    db.commit()
    db.refresh(user)
    return user


@router.post("/request-login-code")
def request_login_code(payload: EmailCodeIn, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    user.email_code = make_email_code()
    db.commit()
    print(f"Login code for {user.email}: {user.email_code}")
    return {"status": "sent"}


@router.post("/login", response_model=TokenOut)
def login(payload: LoginIn, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Неверный email или пароль")
    if user.email_code != payload.email_code:
        raise HTTPException(status_code=401, detail="Неверный код")
    if not user.email_verified:
        raise HTTPException(status_code=403, detail="Подтвердите email")
    if user.approval_status != ApprovalStatus.approved:
        raise HTTPException(status_code=403, detail="Аккаунт ожидает одобрения")
    user.email_code = None
    db.commit()
    return TokenOut(access_token=create_access_token(str(user.id), user.role.value))


@router.post("/admin-login", response_model=TokenOut)
def admin_login(login: str, password: str):
    if not verify_admin_credentials(login, password):
        raise HTTPException(status_code=401, detail="Неверный логин или пароль")
    return TokenOut(access_token=create_access_token("0", UserRole.admin.value))
