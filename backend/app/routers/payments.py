from fastapi import APIRouter, Depends

from app.dependencies import require_role
from app.models import User, UserRole

router = APIRouter(prefix="/payments", tags=["payments"])


@router.post("/checkout")
def create_checkout(tutor_id: int, provider: str = "yookassa", student: User = Depends(require_role(UserRole.student))):
    # Здесь подключается реальный SDK/HTTP API ЮKassa или CloudPayments.
    # Секреты должны лежать только на сервере в .env, не во фронтенде.
    return {
        "status": "draft",
        "provider": provider,
        "student_id": student.id,
        "tutor_id": tutor_id,
        "payment_url": None,
    }


@router.post("/webhook/{provider}")
def payment_webhook(provider: str, payload: dict):
    # TODO: проверить подпись провайдера, найти платеж, создать Enrollment после оплаты.
    return {"status": "accepted", "provider": provider}
