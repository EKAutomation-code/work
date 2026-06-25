import time

from fastapi import FastAPI
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db.session import Base, engine
from app.routers import admin, auth, chats, files, homework, payments, tutors
from app.db.session import SessionLocal
from app.seed import seed_demo_data

def patch_existing_schema() -> None:
    statements = [
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS avatar_file_key VARCHAR(500)",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS about TEXT",
        "ALTER TABLE tutor_profiles ADD COLUMN IF NOT EXISTS bio TEXT",
        "ALTER TABLE tutor_profiles ADD COLUMN IF NOT EXISTS education TEXT",
        "ALTER TABLE tutor_profiles ADD COLUMN IF NOT EXISTS experience TEXT",
        "ALTER TABLE tutor_profiles ADD COLUMN IF NOT EXISTS lesson_format TEXT",
        "ALTER TABLE enrollments ADD COLUMN IF NOT EXISTS next_lesson_at TIMESTAMP",
        "ALTER TABLE homeworks ADD COLUMN IF NOT EXISTS attachment_file_key VARCHAR(500)",
        "ALTER TABLE homeworks ADD COLUMN IF NOT EXISTS attachment_file_name VARCHAR(255)",
        "ALTER TABLE homeworks ADD COLUMN IF NOT EXISTS target_student_id INTEGER",
        "ALTER TABLE homework_submissions ADD COLUMN IF NOT EXISTS teacher_comment TEXT",
    ]
    with engine.begin() as connection:
        for statement in statements:
            connection.execute(text(statement))


def init_database(retries: int = 20, delay_seconds: int = 3) -> None:
    for attempt in range(1, retries + 1):
        try:
            Base.metadata.create_all(bind=engine)
            patch_existing_schema()
            db = SessionLocal()
            try:
                seed_demo_data(db)
            finally:
                db.close()
            return
        except OperationalError:
            if attempt == retries:
                raise
            time.sleep(delay_seconds)


init_database()

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix=settings.api_prefix)
app.include_router(admin.router, prefix=settings.api_prefix)
app.include_router(tutors.router, prefix=settings.api_prefix)
app.include_router(chats.router, prefix=settings.api_prefix)
app.include_router(homework.router, prefix=settings.api_prefix)
app.include_router(files.router, prefix=settings.api_prefix)
app.include_router(payments.router, prefix=settings.api_prefix)


@app.get("/health")
def health():
    return {"status": "ok"}
