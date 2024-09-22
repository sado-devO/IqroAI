# schemas.py
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import date, datetime

class UserCreate(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    password: str
    role: str
    birth_date: date
    phone_number: str
    grade: Optional[int] = None
    consent: str
    interests: Optional[str] = None

class UserResponse(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: str
    role: str
    birth_date: date
    phone_number: str
    grade: Optional[int]
    interests: Optional[str]

    class Config:
        orm_mode = True

class ParentCreate(BaseModel):
    user_id: int
    student_id: int

class TeacherCreate(BaseModel):
    user_id: int
    subjects: str

class SubjectCreate(BaseModel):
    name: str
    grade: int
    description: str
    book_text: str
    video_link: Optional[str] = None

class ScheduleAndBookCreate(BaseModel):
    subject_id: int
    grade: int
    title: str
    content: str
    online_lesson_link: Optional[str] = None

class TestCreate(BaseModel):
    user_id: int
    type: str
    questions: str
    answers: Optional[str] = None
    results: Optional[str] = None

class TestResultCreate(BaseModel):
    user_id: int
    test_id: int
    result: dict

class TestResultResponse(BaseModel):
    id: int
    user_id: int
    test_id: int
    result: dict
    created_at: datetime

    class Config:
        orm_mode = True

class PsychologicalAssessmentCreate(BaseModel):
    user_id: int
    questions: str
    answers: Optional[str] = None
    results: Optional[str] = None

class StudentProgressCreate(BaseModel):
    user_id: int
    subject_id: int
    progress: float

class ChatCreate(BaseModel):
    user_id: int
    name: str = "Yangi chat"

class ChatResponse(BaseModel):
    id: int
    user_id: int
    name: str
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class MessageCreate(BaseModel):
    chat_id: int
    role: str
    content: str

class MessageResponse(BaseModel):
    id: int
    chat_id: int
    role: str
    content: str
    timestamp: datetime

    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class AIQuery(BaseModel):
    query: str
    chat_id: Optional[int] = None

class StudentReportResponse(BaseModel):
    id: int
    user_id: int
    subject: str
    percentage: float
    grade: int
    created_at: datetime

    class Config:
        orm_mode = True


class TokenData(BaseModel):
    email: Optional[str] = None
