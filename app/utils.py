import streamlit as st
import requests
import json
from datetime import datetime
import pandas as pd
import plotly.express as px
import numpy as np

# FastAPI backend URL
API_URL = "http://localhost:8000"

# Language dictionaries
languages = {
    "en": {
        "title": "IqroAI Learning Assistant",
        "login": "Login",
        "register": "Register",
        "email": "Email",
        "password": "Password",
        "first_name": "First Name",
        "last_name": "Last Name",
        "birth_date": "Birth Date",
        "phone_number": "Phone Number",
        "grade": "Grade",
        "interests": "Interests (comma-separated)",
        "consent": "I agree to the terms and conditions",
        "submit": "Submit",
        "logout": "Logout",
        "chat": "Chat",
        "profile": "Profile",
        "reports": "Reports",
        "new_chat": "New Chat",
        "generate_report": "Generate New Report",
        "no_reports": "No reports available. Please generate a new report.",
        "welcome": "Welcome to IqroAI Learning Assistant!",
        "description": "IqroAI is your personal AI-powered learning companion. It's designed to help students in Uzbekistan with their studies, providing personalized assistance, and tracking academic progress.",
        "ask_iqroai": "What would you like to ask IqroAI?",
        "update_profile": "Update Profile",
        "profile_updated": "Profile updated successfully!",
        "profile_update_failed": "Failed to update profile: ",
        "subject_performance": "Subject Performance",
        "percentage": "Percentage",
        "subject": "Subject",
        "report_table": "Report Table",
        "grade_performance": "Grade Performance"
    },
    "uz": {
        "title": "IqroAI O'quv Yordamchisi",
        "login": "Kirish",
        "register": "Ro'yxatdan o'tish",
        "email": "Elektron pochta",
        "password": "Parol",
        "first_name": "Ism",
        "last_name": "Familiya",
        "birth_date": "Tug'ilgan sana",
        "phone_number": "Telefon raqami",
        "grade": "Sinf",
        "interests": "Qiziqishlar (vergul bilan ajratilgan)",
        "consent": "Men shartlarga roziman",
        "submit": "Yuborish",
        "logout": "Chiqish",
        "chat": "Suhbat",
        "profile": "Profil",
        "reports": "Hisobotlar",
        "new_chat": "Yangi suhbat",
        "generate_report": "Yangi hisobot yaratish",
        "no_reports": "Hisobotlar mavjud emas. Iltimos, yangi hisobot yarating.",
        "welcome": "IqroAI O'quv Yordamchisiga xush kelibsiz!",
        "description": "IqroAI - bu shaxsiy AI-quvvatli o'quv yordamchingiz. U O'zbekistondagi o'quvchilarga o'qishlarida yordam berish, shaxsiy yordam ko'rsatish va akademik yutuqlarni kuzatib borish uchun mo'ljallangan.",
        "ask_iqroai": "IqroAI'dan nimani so'ramoqchisiz?",
        "update_profile": "Profilni yangilash",
        "profile_updated": "Profil muvaffaqiyatli yangilandi!",
        "profile_update_failed": "Profilni yangilashda xatolik yuz berdi: ",
        "subject_performance": "Fan bo'yicha natijalar",
        "percentage": "Foiz",
        "subject": "Fan",
        "report_table": "Hisobot jadvali",
        "grade_performance": "Baho ko'rsatkichi"
    },
    "ru": {
        "title": "Обучающий ассистент IqroAI",
        "login": "Вход",
        "register": "Регистрация",
        "email": "Электронная почта",
        "password": "Пароль",
        "first_name": "Имя",
        "last_name": "Фамилия",
        "birth_date": "Дата рождения",
        "phone_number": "Номер телефона",
        "grade": "Класс",
        "interests": "Интересы (разделенные запятыми)",
        "consent": "Я согласен с условиями",
        "submit": "Отправить",
        "logout": "Выйти",
        "chat": "Чат",
        "profile": "Профиль",
        "reports": "Отчеты",
        "new_chat": "Новый чат",
        "generate_report": "Создать новый отчет",
        "no_reports": "Отчеты отсутствуют. Пожалуйста, создайте новый отчет.",
        "welcome": "Добро пожаловать в обучающий ассистент IqroAI!",
        "description": "IqroAI - это ваш личный AI-помощник в обучении. Он разработан для помощи ученикам в Узбекистане в их учебе, предоставляя персонализированную поддержку и отслеживая академический прогресс.",
        "ask_iqroai": "Что бы вы хотели спросить у IqroAI?",
        "update_profile": "Обновить профиль",
        "profile_updated": "Профиль успешно обновлен!",
        "profile_update_failed": "Не удалось обновить профиль: ",
        "subject_performance": "Успеваемость по предметам",
        "percentage": "Процент",
        "subject": "Предмет",
        "report_table": "Таблица отчета",
        "grade_performance": "Показатель успеваемости"
    }
}
def set_page_config():
    st.set_page_config(layout="wide", page_title="IqroAI", page_icon="🧠")

def add_custom_css():
    st.markdown("""
    <style>
        .main {
            padding: 2rem;
        }
        .stButton button {
            width: 100%;
            border-radius: 20px;
        }
        .stTextInput, .stTextArea, .stDateInput, .stNumberInput {
            border-radius: 10px;
        }
        .reportcard {
            padding: 1rem;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        .scarf-banner {
            background: linear-gradient(45deg, #f3ec78, #af4261);
            padding: 10px;
            border-radius: 10px;
            margin-bottom: 20px;
            text-align: center;
            font-weight: bold;
            color: white;
        }
        .tit {
            color: #ffffff
        }
    </style>
    """, unsafe_allow_html=True)

def add_scarf_banner():
    st.markdown('<div class="scarf-banner"><h1 class="tit">IqroAI Learning Assistant</h1></div>', unsafe_allow_html=True)

def initialize_session_state():
    if "user_id" not in st.session_state:
        st.session_state.user_id = None
    if "chat_id" not in st.session_state:
        st.session_state.chat_id = None
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "chats" not in st.session_state:
        st.session_state.chats = []
    if "user_data" not in st.session_state:
        st.session_state.user_data = None
    if "access_token" not in st.session_state:
        st.session_state.access_token = None
    if "report_data" not in st.session_state:
        st.session_state.report_data = None
    if "language" not in st.session_state:
        st.session_state.language = "en"

def login_user(email, password):
    response = requests.post(f"{API_URL}/token", data={"username": email, "password": password})
    if response.status_code == 200:
        data = response.json()
        st.session_state.access_token = data["access_token"]
        st.session_state.user_id = get_user_info()["id"]
        st.success("Login successful!")
        st.rerun()
    else:
        st.error("Invalid credentials. Please try again.")

def register_user(user_data):
    response = requests.post(f"{API_URL}/register_student", json=user_data)
    if response.status_code == 200:
        st.success("Registration successful! Please log in.")
    else:
        st.error(f"Registration failed: {response.json()['detail']}")

def get_user_info():
    headers = {"Authorization": f"Bearer {st.session_state.access_token}"}
    response = requests.get(f"{API_URL}/users/me/", headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        st.error("Failed to fetch user information")
        return None

def get_user_chats():
    headers = {"Authorization": f"Bearer {st.session_state.access_token}"}
    response = requests.get(f"{API_URL}/chats", headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        st.error("Failed to fetch chats")
        return []

def get_chat_messages(chat_id):
    headers = {"Authorization": f"Bearer {st.session_state.access_token}"}
    response = requests.get(f"{API_URL}/chats/{chat_id}/messages", headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        st.error("Failed to fetch messages")
        return []

def update_chat_name(chat_id, new_name):
    headers = {"Authorization": f"Bearer {st.session_state.access_token}"}
    response = requests.put(f"{API_URL}/chats/{chat_id}", params={"name": new_name}, headers=headers)
    if response.status_code == 200:
        st.success("Chat name updated successfully")
    else:
        st.error("Failed to update chat name")

def delete_chat(chat_id):
    headers = {"Authorization": f"Bearer {st.session_state.access_token}"}
    response = requests.delete(f"{API_URL}/chats/{chat_id}", headers=headers)
    if response.status_code == 200:
        st.success("Chat deleted successfully")
        st.session_state.chat_id = None
        st.session_state.messages = []
        st.rerun()
    else:
        st.error("Failed to delete chat")

def generate_report():
    headers = {"Authorization": f"Bearer {st.session_state.access_token}"}
    with st.spinner("Generating report... This may take a moment."):
        response = requests.post(f"{API_URL}/ai_hisobot", headers=headers)
    if response.status_code == 200:
        st.session_state.report_data = response.json()
        st.success("Report generated successfully!")
    else:
        st.error("Failed to generate report")

def get_student_reports():
    headers = {"Authorization": f"Bearer {st.session_state.access_token}"}
    response = requests.get(f"{API_URL}/student_reports", headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        st.error("Failed to fetch student reports")
        return []

def language_selector():
    cols = st.columns(3)
    if cols[0].button("🇺🇿 O'zbek"):
        st.session_state.language = "uz"
        st.rerun()
    if cols[1].button("🇬🇧 English"):
        st.session_state.language = "en"
        st.rerun()
    if cols[2].button("🇷🇺 Русский"):
        st.session_state.language = "ru"
        st.rerun()

def display_chat_interface(lang):
    st.subheader(lang["chat"])
    
    with st.sidebar:
        st.subheader(lang["chat"])
        
        st.session_state.chats = get_user_chats()
        
        for chat in st.session_state.chats:
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                if st.button(chat["name"], key=f"chat_{chat['id']}"):
                    st.session_state.chat_id = chat["id"]
                    st.session_state.messages = get_chat_messages(chat["id"])
                    st.rerun()
            with col2:
                if st.button("🖊", key=f"edit_{chat['id']}"):
                    new_name = st.text_input("New chat name", value=chat["name"], key=f"new_name_{chat['id']}")
                    if st.button("Update", key=f"update_{chat['id']}"):
                        update_chat_name(chat["id"], new_name)
                        st.rerun()
            with col3:
                if st.button("🗑", key=f"delete_{chat['id']}"):
                    delete_chat(chat["id"])
        
        if st.button(lang["new_chat"]):
            st.session_state.chat_id = None
            st.session_state.messages = []
            st.rerun()

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input(lang["ask_iqroai"]):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            headers = {"Authorization": f"Bearer {st.session_state.access_token}"}
            data = {
                "query": prompt,
                "chat_id": st.session_state.chat_id
            }
            with requests.post(f"{API_URL}/ai_assistant", json=data, headers=headers, stream=True) as r:
                if r.status_code != 200:
                    st.error("Failed to get response from AI assistant")
                else:
                    for chunk in r.iter_content(chunk_size=1024):
                        if chunk:
                            full_response += chunk.decode()
                            message_placeholder.markdown(full_response + "▌")
                    message_placeholder.markdown(full_response)
        
        st.session_state.messages.append({"role": "assistant", "content": full_response})

        if not st.session_state.chat_id:
            st.session_state.chats = get_user_chats()
            if st.session_state.chats:
                st.session_state.chat_id = st.session_state.chats[-1]["id"]
            st.rerun()

def display_profile(lang):
    st.subheader(lang["profile"])
    
    user_data = get_user_info()
    
    if user_data:
        with st.form("edit_profile_form"):
            first_name = st.text_input(lang["first_name"], value=user_data["first_name"])
            last_name = st.text_input(lang["last_name"], value=user_data["last_name"])
            email = st.text_input(lang["email"], value=user_data["email"])
            birth_date = st.date_input(lang["birth_date"], value=datetime.strptime(user_data["birth_date"], "%Y-%m-%d").date())
            phone_number = st.text_input(lang["phone_number"], value=user_data["phone_number"])
            grade = st.number_input(lang["grade"], value=user_data["grade"], min_value=1, max_value=12)
            interests = st.text_area(lang["interests"], value=user_data.get("interests", ""))
            
            update_button = st.form_submit_button(lang["update_profile"])
            
            if update_button:
                updated_data = {
                    "first_name": first_name,
                    "last_name": last_name,
                    "email": email,
                    "birth_date": str(birth_date),
                    "phone_number": phone_number,
                    "grade": grade,
                    "interests": interests
                }
                headers = {"Authorization": f"Bearer {st.session_state.access_token}"}
                response = requests.put(f"{API_URL}/users/me", json=updated_data, headers=headers)
                if response.status_code == 200:
                    st.success(lang["profile_updated"])
                else:
                    st.error(f"{lang['profile_update_failed']}{response.json()['detail']}")

def display_reports(lang):
    st.subheader(lang["reports"])

    if st.button(lang["generate_report"]):
        generate_report()

    reports = get_student_reports()
    
    if reports:
        display_report_charts(reports, lang)
    else:
        st.warning(lang["no_reports"])

def display_report_charts(report_data, lang):
    if report_data:
        df = pd.DataFrame(report_data)
        
        # Assuming the original column names are 'subject', 'percentage', and 'grade'
        subject_col = 'subject'
        percentage_col = 'percentage'
        grade_col = 'grade'
        
        # Check if the assumed column names exist, if not, try to find similar columns
        if subject_col not in df.columns:
            subject_col = df.columns[0]  # Assume the first column is the subject
        if percentage_col not in df.columns:
            percentage_col = df.select_dtypes(include=[np.number]).columns[0]  # Assume the first numeric column is percentage
        if grade_col not in df.columns:
            grade_col = df.select_dtypes(include=[np.number]).columns[-1]  # Assume the last numeric column is grade
        
        fig_percentage = px.bar(df, x=subject_col, y=percentage_col, 
                                title=f"{lang['subject_performance']} ({lang['percentage']})")
        fig_percentage.update_xaxes(title_text=lang['subject'])
        fig_percentage.update_yaxes(title_text=lang['percentage'])
        st.plotly_chart(fig_percentage, use_container_width=True)
        
        fig_grade = px.line(df, x=subject_col, y=grade_col, 
                            title=f"{lang['subject_performance']} ({lang['grade']})", markers=True)
        fig_grade.update_xaxes(title_text=lang['subject'])
        fig_grade.update_yaxes(title_text=lang['grade'])
        st.plotly_chart(fig_grade, use_container_width=True)
        
        st.subheader(lang["report_table"])
        
        # Create a new DataFrame with translated column names for display
        display_df = df[[subject_col, percentage_col, grade_col]].copy()
        display_df.columns = [lang['subject'], lang['percentage'], lang['grade']]
        st.table(display_df)
    else:
        st.warning(lang["no_reports"])
