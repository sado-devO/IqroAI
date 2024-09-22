import streamlit as st
from streamlit_option_menu import option_menu
from utils import (
    set_page_config, add_custom_css, add_scarf_banner, initialize_session_state,
    login_user, register_user, get_user_info, get_user_chats, get_chat_messages,
    update_chat_name, delete_chat, generate_report, get_student_reports,
    language_selector, display_chat_interface, display_profile, display_reports,
    languages
)

# Set page config
set_page_config()

# Add custom CSS
add_custom_css()

# Add scarf banner
add_scarf_banner()

# Initialize session state
initialize_session_state()

def main():
    
    lang = languages[st.session_state.language]

    if not st.session_state.user_id:
        language_selector()
        
        st.write(lang["welcome"])
        st.write(lang["description"])
        
        tab1, tab2 = st.tabs([lang["login"], lang["register"]])
        
        with tab1:
            st.subheader(lang["login"])
            email = st.text_input(lang["email"], key="login_email")
            password = st.text_input(lang["password"], type="password", key="login_password")
            if st.button(lang["login"]):
                login_user(email, password)
        
        with tab2:
            st.subheader(lang["register"])
            with st.form("registration_form"):
                first_name = st.text_input(lang["first_name"])
                last_name = st.text_input(lang["last_name"])
                email = st.text_input(lang["email"])
                password = st.text_input(lang["password"], type="password")
                birth_date = st.date_input(lang["birth_date"])
                phone_number = st.text_input(lang["phone_number"])
                grade = st.number_input(lang["grade"], min_value=1, max_value=12)
                interests = st.text_area(lang["interests"])
                consent = st.checkbox(lang["consent"])
                
                submit_button = st.form_submit_button(lang["submit"])
                
                if submit_button:
                    if not consent:
                        st.error("You must agree to the terms and conditions to register.")
                    else:
                        user_data = {
                            "first_name": first_name,
                            "last_name": last_name,
                            "email": email,
                            "password": password,
                            "role": "student",
                            "birth_date": str(birth_date),
                            "phone_number": phone_number,
                            "grade": grade,
                            "interests": interests,
                            "consent": "true"
                        }
                        register_user(user_data)
    else:
        selected = option_menu(
            menu_title=None,
            options=[lang["chat"], lang["profile"], lang["reports"], lang["logout"]],
            icons=['chat', 'person', 'file-text', 'box-arrow-right'],
            menu_icon="cast",
            default_index=0,
            orientation="horizontal",
        )
        
        if selected == lang["logout"]:
            st.session_state.clear()
            st.rerun()
        elif selected == lang["chat"]:
            display_chat_interface(lang)
        elif selected == lang["profile"]:
            display_profile(lang)
        elif selected == lang["reports"]:
            display_reports(lang)

if __name__ == "__main__":
    main()
