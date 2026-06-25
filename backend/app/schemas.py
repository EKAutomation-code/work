from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from app.models import ApprovalStatus, Subject, UserRole


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: int
    role: UserRole
    email: EmailStr
    full_name: str
    about: str | None = None
    avatar_url: str | None = None
    approval_status: ApprovalStatus
    email_verified: bool
    kyc_verified: bool

    class Config:
        from_attributes = True


class CurrentUserOut(UserOut):
    token_role: UserRole


class RegisterIn(BaseModel):
    role: UserRole
    email: EmailStr
    full_name: str = Field(min_length=2)
    password: str = Field(min_length=8)


class LoginIn(BaseModel):
    email: EmailStr
    password: str
    email_code: str = Field(min_length=6, max_length=6)


class VerifyEmailIn(BaseModel):
    email: EmailStr
    code: str = Field(min_length=6, max_length=6)


class EmailCodeIn(BaseModel):
    email: EmailStr


class TutorOfferIn(BaseModel):
    subject: Subject
    price_rub: int = Field(ge=100)
    description: str = Field(min_length=10, max_length=1200)
    offer_published: bool = True


class TutorOfferPackageIn(BaseModel):
    title: str = Field(min_length=3, max_length=255)
    subject: Subject
    price_rub: int = Field(ge=100)
    description: str = Field(min_length=10, max_length=1200)


class TutorOfferPackageOut(BaseModel):
    id: int
    title: str
    subject: Subject
    price_rub: int
    description: str

    class Config:
        from_attributes = True


class TutorCardOut(BaseModel):
    id: int
    full_name: str
    avatar_url: str | None = None
    subject: Subject
    price_rub: int
    description: str
    average_rating: float = 0
    review_count: int = 0
    is_enrolled: bool = False
    offer_count: int = 1


class TutorOfferOut(BaseModel):
    subject: Subject | None = None
    price_rub: int | None = None
    description: str = ""
    bio: str = ""
    education: str = ""
    experience: str = ""
    lesson_format: str = ""
    offer_published: bool = False
    packages: list[TutorOfferPackageOut] = []


class ReviewOut(BaseModel):
    id: int
    student_id: int
    student_name: str
    stars: int
    text: str
    created_at: datetime
    student_avatar_url: str | None = None


class TutorProfileOut(BaseModel):
    id: int
    full_name: str
    avatar_url: str | None = None
    subject: Subject | None = None
    price_rub: int | None = None
    description: str = ""
    bio: str = ""
    education: str = ""
    experience: str = ""
    lesson_format: str = ""
    average_rating: float = 0
    review_count: int = 0
    is_enrolled: bool = False
    can_review: bool = False
    reviews: list[ReviewOut] = []
    packages: list[TutorOfferPackageOut] = []


class TutorReviewIn(BaseModel):
    stars: int = Field(ge=1, le=5)
    text: str = Field(min_length=6, max_length=800)


class ProfileUpdateIn(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=255)
    about: str | None = Field(default=None, max_length=1200)
    avatar_file_key: str | None = None


class TutorProfileUpdateIn(BaseModel):
    bio: str = Field(min_length=10, max_length=2000)
    education: str = Field(min_length=4, max_length=1200)
    experience: str = Field(min_length=4, max_length=1200)
    lesson_format: str = Field(min_length=4, max_length=1200)


class TutorStudentOut(BaseModel):
    student_id: int
    full_name: str
    email: EmailStr
    avatar_url: str | None = None
    enrolled_at: datetime
    next_lesson_at: datetime | None = None


class NextLessonUpdateIn(BaseModel):
    next_lesson_at: datetime | None = None


class HomeworkIn(BaseModel):
    title: str = Field(min_length=3, max_length=255)
    description: str = Field(min_length=5)
    attachment_file_key: str | None = None
    attachment_file_name: str | None = None
    target_student_id: int | None = None


class HomeworkOut(BaseModel):
    id: int
    title: str
    description: str
    target_student_id: int | None = None
    target_student_name: str | None = None
    attachment_file_name: str | None = None
    attachment_file_url: str | None = None
    is_image: bool = False
    created_at: datetime

    class Config:
        from_attributes = True


class SubmissionIn(BaseModel):
    homework_id: int
    file_key: str
    file_name: str


class GradeIn(BaseModel):
    grade: int = Field(ge=1, le=5)
    teacher_comment: str | None = Field(default=None, max_length=2000)


class HomeworkSubmissionOut(BaseModel):
    id: int
    student_id: int
    student_name: str
    file_name: str
    file_url: str | None = None
    is_image: bool = False
    grade: int | None = None
    teacher_comment: str | None = None
    created_at: datetime


class StudentHomeworkOut(HomeworkOut):
    tutor_id: int
    tutor_name: str
    submission: HomeworkSubmissionOut | None = None


class TutorHomeworkOut(HomeworkOut):
    submissions: list[HomeworkSubmissionOut] = []


class PresignIn(BaseModel):
    file_name: str
    content_type: str
    purpose: str = "homework"


class PresignOut(BaseModel):
    upload_url: str
    file_key: str


class LeaderboardItem(BaseModel):
    student_id: int
    full_name: str
    average_grade: float
    graded_count: int


class AdminApprovalIn(BaseModel):
    status: ApprovalStatus
    kyc_verified: bool | None = None


class ChatSummaryOut(BaseModel):
    id: int
    partner_id: int
    partner_name: str
    partner_avatar_url: str | None = None
    partner_role: UserRole
    subject: Subject | None = None
    price_rub: int | None = None
    last_message_text: str | None = None
    last_message_file_name: str | None = None
    last_message_at: datetime | None = None


class ChatMessageOut(BaseModel):
    id: int
    sender_id: int
    sender_name: str
    sender_avatar_url: str | None = None
    text: str | None = None
    file_key: str | None = None
    file_name: str | None = None
    file_url: str | None = None
    is_image: bool = False
    created_at: datetime


class ChatMessageIn(BaseModel):
    text: str | None = None
    file_key: str | None = None
    file_name: str | None = None
