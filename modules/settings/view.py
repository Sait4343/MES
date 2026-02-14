import streamlit as st
from core.config import ROLE_LABELS

def render():
    st.header("⚙️ Налаштування")
    
    user = st.session_state.user_profile
    if not user:
        st.error("Помилка завантаження профілю.")
        return
        
    st.subheader("Мій профіль")
    
    st.text_input("Повне ім'я", value=user.get("full_name", ""), disabled=True)
    st.text_input("Email", value=user.get("email", ""), disabled=True)
    
    role = user.get("role", "worker")
    st.text_input("Роль", value=ROLE_LABELS.get(role, role), disabled=True)
    
    st.divider()
    
    st.caption(f"User ID: {user.get('id')}")
    st.caption("Для зміни паролю або імені зверніться до адміністратора.")
