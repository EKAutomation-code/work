from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import decode_access_token, verify_password
from app.db.session import get_db
from app.models import ApprovalStatus, User, UserRole


oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.api_prefix}/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Нужно войти")
    user = db.get(User, int(payload["sub"]))
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Пользователь не найден")
    return user


def require_approved(user: User = Depends(get_current_user)) -> User:
    if user.approval_status != ApprovalStatus.approved or not user.email_verified:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Аккаунт еще не одобрен")
    return user


def require_role(role: UserRole):
    def checker(user: User = Depends(require_approved)) -> User:
        if user.role != role:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав")
        return user

    return checker


def require_admin(token: str = Depends(oauth2_scheme)) -> dict:
    payload = decode_access_token(token)
    if payload and payload.get("role") == UserRole.admin.value:
        return payload
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нужна админ-панель")


def verify_admin_credentials(login: str, password: str) -> bool:
    return login == settings.admin_login and password == settings.admin_password
