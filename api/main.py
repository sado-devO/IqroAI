import os
import json
import logging
from datetime import timedelta
from typing import List
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, status
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi.middleware.cors import CORSMiddleware
import anthropic

from database import SessionLocal, engine, Base, User, Chat, Message, Test, TestResult, StudentReport, Parent, Teacher, Subject, ScheduleAndBooks, PsychologicalAssessment, StudentProgress
from schemas import (UserCreate, UserResponse, ParentCreate, TeacherCreate, SubjectCreate,
                     ScheduleAndBookCreate, TestCreate, TestResultCreate, TestResultResponse,
                     PsychologicalAssessmentCreate, StudentProgressCreate, ChatCreate,
                     ChatResponse, MessageCreate, MessageResponse, Token, TokenData,
                     AIQuery, StudentReportResponse)
from utils import (get_db, verify_password, get_password_hash, authenticate_user,
                   create_access_token, get_current_user, get_student_context,
                   get_chat_history, create_new_chat, save_test, calculate_age)

from sqladmin import Admin, ModelView
from fastapi import FastAPI

from prompts import get_ai_report_prompt, get_system_prompt

# Environment o'zgaruvchilarini yuklash
from dotenv import load_dotenv
load_dotenv()

# FastAPI ilovasi sozlamalari
app = FastAPI(title="IqroAI API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Autentifikatsiya sozlamalari
SECRET_KEY = os.environ.get("SECRET_KEY", "your-secret-key-here")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

api_key = os.environ.get('ANTHROPIC_API_KEY')
anthropic_client = anthropic.Anthropic(api_key=api_key)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.post("/register_student", response_model=UserResponse)
async def register_student(student: UserCreate, db: Session = Depends(get_db)):
    db_student = User(**student.dict(exclude={"password"}))
    db_student.password = get_password_hash(student.password)
    db_student.role = "student"
    db.add(db_student)
    try:
        db.commit()
        db.refresh(db_student)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Email yoki telefon raqami allaqachon ro'yxatdan o'tgan")
    return db_student

@app.post("/register_parent", response_model=ParentCreate)
async def register_parent(parent: ParentCreate, db: Session = Depends(get_db)):
    db_parent = Parent(**parent.dict())
    db.add(db_parent)
    try:
        db.commit()
        db.refresh(db_parent)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Ota-ona va o'quvchi munosabati allaqachon mavjud")
    return db_parent

@app.post("/register_teacher", response_model=TeacherCreate)
async def register_teacher(teacher: TeacherCreate, db: Session = Depends(get_db)):
    db_teacher = Teacher(**teacher.dict())
    db.add(db_teacher)
    try:
        db.commit()
        db.refresh(db_teacher)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="O'qituvchi allaqachon ro'yxatdan o'tgan")
    return db_teacher

@app.post("/subjects", response_model=SubjectCreate)
async def create_subject(subject: SubjectCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Faqat adminlar fan qo'shishi mumkin")
    db_subject = Subject(**subject.dict())
    db.add(db_subject)
    db.commit()
    db.refresh(db_subject)
    return db_subject

@app.get("/subjects", response_model=List[SubjectCreate])
async def get_subjects(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    subjects = db.query(Subject).all()
    return subjects

@app.put("/subjects/{subject_id}", response_model=SubjectCreate)
async def update_subject(subject_id: int, subject: SubjectCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Faqat adminlar fanni yangilashi mumkin")
    db_subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if not db_subject:
        raise HTTPException(status_code=404, detail="Fan topilmadi")
    for key, value in subject.dict().items():
        setattr(db_subject, key, value)
    db.commit()
    db.refresh(db_subject)
    return db_subject

@app.delete("/subjects/{subject_id}")
async def delete_subject(subject_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Faqat adminlar fanni o'chirishi mumkin")
    db_subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if not db_subject:
        raise HTTPException(status_code=404, detail="Fan topilmadi")
    db.delete(db_subject)
    db.commit()
    return {"message": "Fan muvaffaqiyatli o'chirildi"}

@app.post("/schedule_and_books", response_model=ScheduleAndBookCreate)
async def create_schedule_and_book(item: ScheduleAndBookCreate, db: Session = Depends(get_db)):
    db_item = ScheduleAndBooks(**item.dict())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

@app.post("/tests", response_model=TestCreate)
async def create_test(test: TestCreate, db: Session = Depends(get_db)):
    db_test = Test(**test.dict())
    db.add(db_test)
    db.commit()
    db.refresh(db_test)
    return db_test

@app.get("/tests", response_model=List[TestCreate])
async def get_tests(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    tests = db.query(Test).filter(Test.user_id == current_user.id).all()
    return tests

@app.get("/tests/{test_id}", response_model=TestCreate)
async def get_test(test_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    test = db.query(Test).filter(Test.id == test_id, Test.user_id == current_user.id).first()
    if not test:
        raise HTTPException(status_code=404, detail="Test topilmadi")
    return test

@app.put("/tests/{test_id}", response_model=TestCreate)
async def update_test(test_id: int, test: TestCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_test = db.query(Test).filter(Test.id == test_id, Test.user_id == current_user.id).first()
    if not db_test:
        raise HTTPException(status_code=404, detail="Test topilmadi")
    for key, value in test.dict().items():
        setattr(db_test, key, value)
    db.commit()
    db.refresh(db_test)
    return db_test

@app.post("/test_results", response_model=TestResultResponse)
async def create_test_result(test_result: TestResultCreate, db: Session = Depends(get_db)):
    db_test_result = TestResult(**test_result.dict())
    db.add(db_test_result)
    db.commit()
    db.refresh(db_test_result)
    return db_test_result

@app.get("/test_results/{user_id}", response_model=List[TestResultResponse])
async def get_user_test_results(user_id: int, db: Session = Depends(get_db)):
    test_results = db.query(TestResult).filter(TestResult.user_id == user_id).all()
    return test_results

@app.put("/test_results/{result_id}", response_model=TestResultResponse)
async def update_test_result(result_id: int, test_result: TestResultCreate, db: Session = Depends(get_db)):
    db_test_result = db.query(TestResult).filter(TestResult.id == result_id).first()
    if not db_test_result:
        raise HTTPException(status_code=404, detail="Test natijasi topilmadi")
    for key, value in test_result.dict().items():
        setattr(db_test_result, key, value)
    db.commit()
    db.refresh(db_test_result)
    return db_test_result

@app.get("/psychological_assessments", response_model=List[PsychologicalAssessmentCreate])
async def get_psychological_assessments(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    assessments = db.query(PsychologicalAssessment).filter(PsychologicalAssessment.user_id == current_user.id).all()
    return assessments

@app.get("/psychological_assessments/{assessment_id}", response_model=PsychologicalAssessmentCreate)
async def get_psychological_assessment(assessment_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    assessment = db.query(PsychologicalAssessment).filter(PsychologicalAssessment.id == assessment_id, PsychologicalAssessment.user_id == current_user.id).first()
    if not assessment:
        raise HTTPException(status_code=404, detail="Psixologik baholash topilmadi")
    return assessment

@app.put("/psychological_assessments/{assessment_id}", response_model=PsychologicalAssessmentCreate)
async def update_psychological_assessment(assessment_id: int, assessment: PsychologicalAssessmentCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_assessment = db.query(PsychologicalAssessment).filter(PsychologicalAssessment.id == assessment_id, PsychologicalAssessment.user_id == current_user.id).first()
    if not db_assessment:
        raise HTTPException(status_code=404, detail="Psixologik baholash topilmadi")
    for key, value in assessment.dict().items():
        setattr(db_assessment, key, value)
    db.commit()
    db.refresh(db_assessment)
    return db_assessment

@app.get("/student_progress/{student_id}", response_model=List[StudentProgressCreate])
async def get_student_progress(student_id: int, db: Session = Depends(get_db)):
    progress = db.query(StudentProgress).filter(StudentProgress.user_id == student_id).all()
    return progress

@app.post("/student_progress", response_model=StudentProgressCreate)
async def create_student_progress(progress: StudentProgressCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role != "teacher" and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Faqat o'qituvchilar va adminlar progress yozuvlarini yaratishi mumkin")
    db_progress = StudentProgress(**progress.dict())
    db.add(db_progress)
    db.commit()
    db.refresh(db_progress)
    return db_progress

@app.put("/student_progress/{progress_id}", response_model=StudentProgressCreate)
async def update_student_progress(progress_id: int, progress: StudentProgressCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role != "teacher" and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Faqat o'qituvchilar va adminlar progress yozuvlarini yangilashi mumkin")
    db_progress = db.query(StudentProgress).filter(StudentProgress.id == progress_id).first()
    if not db_progress:
        raise HTTPException(status_code=404, detail="Progress yozuvi topilmadi")
    for key, value in progress.dict().items():
        setattr(db_progress, key, value)
    db.commit()
    db.refresh(db_progress)
    return db_progress

@app.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    logger.info(f"Foydalanuvchi uchun login urinishi: {form_data.username}")
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        logger.warning(f"Foydalanuvchi uchun login urinishi muvaffaqiyatsiz: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Noto'g'ri foydalanuvchi nomi yoki parol",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    logger.info(f"Foydalanuvchi uchun login muvaffaqiyatli: {form_data.username}")
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/ai_assistant")
async def query_ai_assistant(query: AIQuery, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if query.chat_id:
        chat = db.query(Chat).filter(Chat.id == query.chat_id, Chat.user_id == current_user.id).first()
        if not chat:
            raise HTTPException(status_code=404, detail="Chat topilmadi")
    else:
        chat = create_new_chat(current_user.id, db)

    context = get_student_context(current_user.id, db)
    chat_history = get_chat_history(chat.id, db)
    
    system_prompt = get_system_prompt(json.dumps(context, indent=2))

    conversation_history = chat_history + [{"role": "user", "content": query.query}]

    response_text = ""

    def generate():
        nonlocal response_text
        try:
            with anthropic_client.messages.stream(
                model="claude-3-5-sonnet-20240620",
                max_tokens=2000,
                temperature=0.7,
                system=system_prompt,
                messages=conversation_history
            ) as stream:
                for text in stream.text_stream:
                    response_text += text
                    yield text

            # Foydalanuvchi xabarini saqlash
            user_message = Message(chat_id=chat.id, role="user", content=query.query)
            db.add(user_message)
            
            # Assistent javobini saqlash
            assistant_message = Message(chat_id=chat.id, role="assistant", content=response_text)
            db.add(assistant_message)
            
            # Oldingi xabar Bilimlarni baholash testi bo'lganligini tekshirish
            last_message = db.query(Message).filter(Message.chat_id == chat.id).order_by(Message.timestamp.desc()).offset(1).first()
            if last_message:
                if "Bilimlarni baholash testi" in last_message.content:
                    # Joriy so'rov foydalanuvchining akademik testga javobi
                    test = db.query(Test).filter(Test.user_id == current_user.id, Test.type == "academic").order_by(Test.timestamp.desc()).first()
                    if test:
                        test_result = TestResult(user_id=current_user.id, test_id=test.id, result={"answer": query.query})
                        db.add(test_result)
                elif "Psixologik test" in last_message.content:
                    # Joriy so'rov foydalanuvchining psixologik testga javobi
                    test = db.query(Test).filter(Test.user_id == current_user.id, Test.type == "psychological").order_by(Test.timestamp.desc()).first()
                    if test:
                        test_result = TestResult(user_id=current_user.id, test_id=test.id, result={"answer": query.query})
                        db.add(test_result)

            # Joriy javobda yangi test borligini tekshirish
            if "Bilimlarni baholash testi" in response_text:
                new_test = Test(user_id=current_user.id, type="academic", questions=response_text)
                db.add(new_test)
            elif "Psixologik test" in response_text:
                new_test = Test(user_id=current_user.id, type="psychological", questions=response_text)
                db.add(new_test)
            
            db.commit()

        except Exception as e:
            logger.error(f"AI javob generatsiyasida xatolik: {str(e)}")
            yield "So'rovingizni qayta ishlashda xatolik yuz berdi."

    return StreamingResponse(generate(), media_type="text/plain")

@app.post("/ai_hisobot")
async def generate_ai_report(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # O'quvchi kontekstini olish
    context = get_student_context(current_user.id, db)
    
    # AI model uchun so'rovni tayyorlash
    system_prompt = get_ai_report_prompt(json.dumps(context, indent=2))

    try:
        response = anthropic_client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=2000,
            temperature=0,
            system=system_prompt,
            messages=[{"role": "user", "content": "Ushbu o'quvchi uchun hisobot yarating."}]
        )

        report_data = json.loads(response.content[0].text)

        db.query(StudentReport).filter(StudentReport.user_id == current_user.id).delete()

        # Yangi hisobotlar yaratish
        for subject, data in report_data["Hisobot"].items():
            new_report = StudentReport(
                user_id=current_user.id,
                subject=subject,
                percentage=float(data["foiz"]),
                grade=int(data["ball"])
            )
            db.add(new_report)

        db.commit()

        return JSONResponse(content=report_data)

    except Exception as e:
        logger.error(f"AI hisobot generatsiyasida xatolik: {str(e)}")
        raise HTTPException(status_code=500, detail="Hisobotni yaratishda xatolik yuz berdi")

@app.get("/chats", response_model=List[ChatResponse])
async def get_user_chats(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    chats = db.query(Chat).filter(Chat.user_id == current_user.id).all()
    return chats

@app.get("/chats/{chat_id}/messages", response_model=List[MessageResponse])
async def get_chat_messages(chat_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    chat = db.query(Chat).filter(Chat.id == chat_id, Chat.user_id == current_user.id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat topilmadi")
    return chat.messages

@app.post("/chats/{chat_id}/messages", response_model=MessageResponse)
async def add_message_to_chat(chat_id: int, message: MessageCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    chat = db.query(Chat).filter(Chat.id == chat_id, Chat.user_id == current_user.id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat topilmadi")
    new_message = Message(chat_id=chat_id, role=message.role, content=message.content)
    db.add(new_message)
    db.commit()
    db.refresh(new_message)
    return new_message

@app.put("/chats/{chat_id}", response_model=ChatResponse)
async def update_chat_name(chat_id: int, name: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    chat = db.query(Chat).filter(Chat.id == chat_id, Chat.user_id == current_user.id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat topilmadi")
    chat.name = name
    db.commit()
    db.refresh(chat)
    return chat

@app.delete("/chats/{chat_id}", response_model=dict)
async def delete_chat(chat_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    chat = db.query(Chat).filter(Chat.id == chat_id, Chat.user_id == current_user.id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat topilmadi")
    db.query(Message).filter(Message.chat_id == chat_id).delete()
    db.delete(chat)
    db.commit()
    return {"message": "Chat muvaffaqiyatli o'chirildi"}

@app.get("/users/me/", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

@app.put("/users/me", response_model=UserResponse)
async def update_user(
    user_update: UserCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    for key, value in user_update.dict(exclude_unset=True).items():
        if key == "password":
            value = get_password_hash(value)
        setattr(current_user, key, value)
    try:
        db.commit()
        db.refresh(current_user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Email yoki telefon raqami allaqachon mavjud")
    return current_user

@app.get("/student_reports", response_model=List[StudentReportResponse])
async def get_student_reports(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    reports = db.query(StudentReport).filter(StudentReport.user_id == current_user.id).all()
    return reports

@app.on_event("startup")
async def startup_event():
    Base.metadata.create_all(bind=engine)
    logger.info("Ma'lumotlar bazasi ishga tushirildi.")

class UserAdmin(ModelView, model=User):
    column_list = [User.id, User.first_name, User.last_name, User.email, User.role, User.grade, User.interests]
    column_searchable_list = [User.first_name, User.last_name, User.email, User.interests]
    column_filters = [User.role, User.grade]
    can_create = True
    can_edit = True
    can_delete = True

class ParentAdmin(ModelView, model=Parent):
    column_list = [Parent.id, Parent.user_id, Parent.student_id]
    can_create = True
    can_edit = True
    can_delete = True

class TeacherAdmin(ModelView, model=Teacher):
    column_list = [Teacher.id, Teacher.user_id, Teacher.subjects]
    can_create = True
    can_edit = True
    can_delete = True

class SubjectAdmin(ModelView, model=Subject):
    column_list = [Subject.id, Subject.name, Subject.grade, Subject.description]
    column_searchable_list = [Subject.name]
    column_filters = [Subject.grade]
    can_create = True
    can_edit = True
    can_delete = True

class ScheduleAndBooksAdmin(ModelView, model=ScheduleAndBooks):
    column_list = [ScheduleAndBooks.id, ScheduleAndBooks.subject_id, ScheduleAndBooks.grade, ScheduleAndBooks.title]
    can_create = True
    can_edit = True
    can_delete = True

class TestAdmin(ModelView, model=Test):
    column_list = [Test.id, Test.user_id, Test.type, Test.timestamp]
    column_searchable_list = [Test.user_id, Test.type]
    column_filters = [Test.type, Test.timestamp]
    can_create = True
    can_edit = True
    can_delete = True

class TestResultAdmin(ModelView, model=TestResult):
    column_list = [TestResult.id, TestResult.user_id, TestResult.test_id, TestResult.created_at]
    column_searchable_list = [TestResult.user_id, TestResult.test_id]
    column_filters = [TestResult.created_at]
    can_create = True
    can_edit = True
    can_delete = True

class PsychologicalAssessmentAdmin(ModelView, model=PsychologicalAssessment):
    column_list = [PsychologicalAssessment.id, PsychologicalAssessment.user_id, PsychologicalAssessment.timestamp]
    column_searchable_list = [PsychologicalAssessment.user_id]
    column_filters = [PsychologicalAssessment.timestamp]
    can_create = True
    can_edit = True
    can_delete = True

class StudentProgressAdmin(ModelView, model=StudentProgress):
    column_list = [StudentProgress.id, StudentProgress.user_id, StudentProgress.subject_id, StudentProgress.progress, StudentProgress.last_updated]
    column_searchable_list = [StudentProgress.user_id, StudentProgress.subject_id]
    column_filters = [StudentProgress.last_updated]
    can_create = True
    can_edit = True
    can_delete = True

class ChatAdmin(ModelView, model=Chat):
    column_list = [Chat.id, Chat.user_id, Chat.name, Chat.created_at, Chat.updated_at]
    column_searchable_list = [Chat.user_id, Chat.name]
    column_filters = [Chat.created_at, Chat.updated_at]
    can_create = True
    can_edit = True
    can_delete = True

class MessageAdmin(ModelView, model=Message):
    column_list = [Message.id, Message.chat_id, Message.role, Message.timestamp]
    column_searchable_list = [Message.chat_id, Message.content]
    column_filters = [Message.role, Message.timestamp]
    can_create = True
    can_edit = True
    can_delete = True

class StudentReportAdmin(ModelView, model=StudentReport):
    column_list = [StudentReport.id, StudentReport.user_id, StudentReport.subject, StudentReport.percentage, StudentReport.grade, StudentReport.created_at]
    column_searchable_list = [StudentReport.user_id, StudentReport.subject]
    column_filters = [StudentReport.grade, StudentReport.created_at]
    can_create = True
    can_edit = True
    can_delete = True

# Admin panelni yaratish
admin = Admin(app, engine)

# Admin modellarini qo'shish
admin.add_view(UserAdmin)
admin.add_view(ParentAdmin)
admin.add_view(TeacherAdmin)
admin.add_view(SubjectAdmin)
admin.add_view(ScheduleAndBooksAdmin)
admin.add_view(TestAdmin)
admin.add_view(TestResultAdmin)
admin.add_view(PsychologicalAssessmentAdmin)
admin.add_view(StudentProgressAdmin)
admin.add_view(ChatAdmin)
admin.add_view(MessageAdmin)
admin.add_view(StudentReportAdmin)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
