import os
from datetime import datetime, timedelta
from typing import Optional
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from database import SessionLocal, User, Test, PsychologicalAssessment, StudentProgress, Subject, TestResult, StudentReport, Chat, Message
from schemas import TokenData

SECRET_KEY = os.environ.get("SECRET_KEY", "your-secret-key-here")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def authenticate_user(db: Session, email: str, password: str):
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.password):
        return False
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Haqiqiylikni tasdiqlab bo'lmadi",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception
    user = db.query(User).filter(User.email == token_data.email).first()
    if user is None:
        raise credentials_exception
    return user

def calculate_age(birth_date):
    today = datetime.today()
    return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))

def get_student_context(student_id: int, db: Session):
    student = db.query(User).filter(User.id == student_id).first()
    tests = db.query(Test).filter(Test.user_id == student_id).all()
    psych_assessments = db.query(PsychologicalAssessment).filter(PsychologicalAssessment.user_id == student_id).all()
    progress = db.query(StudentProgress).filter(StudentProgress.user_id == student_id).all()
    subjects = db.query(Subject).filter(Subject.grade == student.grade).all()
    test_results = db.query(TestResult).filter(TestResult.user_id == student_id).all()
    reports = db.query(StudentReport).filter(StudentReport.user_id == student_id).all()
    
    context = {
        "student_info": {
            "name": f"{student.first_name} {student.last_name}",
            "age": calculate_age(student.birth_date),
            "grade": student.grade,
            "interests": student.interests
        },
        "test_results": [{"id": result.id, "test_id": result.test_id, "result": result.result} for result in test_results],
        "psychological_assessments": [assessment.results for assessment in psych_assessments],
        "progress": {prog.subject_id: prog.progress for prog in progress},
        "subjects": [{"name": subject.name, "description": subject.description, "book_text": subject.book_text, "video_link": subject.video_link} for subject in subjects],
        "reports": [{"subject": report.subject, "percentage": report.percentage, "grade": report.grade} for report in reports]
    }
    return context

def get_chat_history(chat_id: int, db: Session):
    messages = db.query(Message).filter(Message.chat_id == chat_id).order_by(Message.timestamp.asc()).all()
    return [{"role": msg.role, "content": msg.content} for msg in messages]

def create_new_chat(user_id: int, db: Session):
    new_chat = Chat(user_id=user_id, name="Yangi chat")
    db.add(new_chat)
    db.commit()
    db.refresh(new_chat)
    return new_chat

def save_test(user_id: int, test_content: str, db: Session):
    test_type = "academic" if "Bilimlarni baholash testi" in test_content else "psychological"
    new_test = Test(user_id=user_id, type=test_type, questions=test_content)
    db.add(new_test)
    db.commit()
