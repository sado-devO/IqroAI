from sqlalchemy import create_engine, Column, Integer, String, Date, ForeignKey, DateTime, Text, Float, JSON
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from datetime import datetime

# Ma'lumotlar bazasi sozlamalari
SQLALCHEMY_DATABASE_URL = "sqlite:///./iqroai.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String)
    last_name = Column(String)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    role = Column(String)
    birth_date = Column(Date)
    phone_number = Column(String, unique=True)
    grade = Column(Integer)
    consent = Column(String)
    interests = Column(String)
    admin_id = Column(String(6), unique=True)

    parents = relationship("Parent", back_populates="student", foreign_keys="Parent.student_id")
    teachers = relationship("Teacher", back_populates="user")
    tests = relationship("Test", back_populates="user")
    psychological_assessments = relationship("PsychologicalAssessment", back_populates="user")
    progress = relationship("StudentProgress", back_populates="user")
    chats = relationship("Chat", back_populates="user")
    test_results = relationship("TestResult", back_populates="user")
    reports = relationship("StudentReport", back_populates="user")

class Parent(Base):
    __tablename__ = "parents"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    student_id = Column(Integer, ForeignKey("users.id"))

    user = relationship("User", foreign_keys=[user_id])
    student = relationship("User", foreign_keys=[student_id], back_populates="parents")

class Teacher(Base):
    __tablename__ = "teachers"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    subjects = Column(String)

    user = relationship("User", back_populates="teachers")

class Subject(Base):
    __tablename__ = "subjects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    grade = Column(Integer)
    description = Column(Text)
    book_text = Column(Text)
    video_link = Column(String)

    schedule_and_books = relationship("ScheduleAndBooks", back_populates="subject")
    progress = relationship("StudentProgress", back_populates="subject")

class ScheduleAndBooks(Base):
    __tablename__ = "schedule_and_books"

    id = Column(Integer, primary_key=True, index=True)
    subject_id = Column(Integer, ForeignKey("subjects.id"))
    grade = Column(Integer)
    title = Column(String)
    content = Column(Text)
    online_lesson_link = Column(String)

    subject = relationship("Subject", back_populates="schedule_and_books")

class Test(Base):
    __tablename__ = "tests"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    type = Column(String)
    questions = Column(Text)
    answers = Column(Text)
    results = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="tests")
    test_results = relationship("TestResult", back_populates="test")

class TestResult(Base):
    __tablename__ = "test_results"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    test_id = Column(Integer, ForeignKey("tests.id"))
    result = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="test_results")
    test = relationship("Test", back_populates="test_results")

class PsychologicalAssessment(Base):
    __tablename__ = "psychological_assessments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    questions = Column(Text)
    answers = Column(Text)
    results = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="psychological_assessments")

class StudentProgress(Base):
    __tablename__ = "student_progress"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    subject_id = Column(Integer, ForeignKey("subjects.id"))
    progress = Column(Float)
    last_updated = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="progress")
    subject = relationship("Subject", back_populates="progress")

class Chat(Base):
    __tablename__ = "chats"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String, default="Yangi chat")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="chats")
    messages = relationship("Message", back_populates="chat")

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(Integer, ForeignKey("chats.id"))
    role = Column(String)
    content = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)

    chat = relationship("Chat", back_populates="messages")

class StudentReport(Base):
    __tablename__ = "student_reports"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    subject = Column(String)
    percentage = Column(Float)
    grade = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="reports")
