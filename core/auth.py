import streamlit as st
import time
from core.database import DatabaseService

db = DatabaseService()

def init_auth():
    """Initialize session state for auth."""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "user" not in st.session_state:
        st.session_state.user = None
    if "role" not in st.session_state:
        st.session_state.role = None
    if "user_profile" not in st.session_state:
        st.session_state.user_profile = None

def login_form():
    """Display login form and handle authentication."""
    st.title("🔐 Вхід в систему")
    
    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Увійти")
        
        if submitted:
            try:
                # 1. Authenticate with Supabase Auth
                res = db.client.auth.sign_in_with_password({"email": email, "password": password})
                user = res.user
                
                if user:
                    # 2. Fetch User Profile (Role)
                    profile = db.get_user_profile(user.id)
                    
                    # 3. Update Session State
                    st.session_state.authenticated = True
                    st.session_state.user = user
                    st.session_state.user_profile = profile
                    st.session_state.role = profile.get("role") if profile else "worker"
                    
                    st.success("Успішний вхід!")
                    time.sleep(1)
                    st.rerun()
            except Exception as e:
                st.error(f"Помилка входу: {e}")

def logout():
    """Log out the user and clear session."""
    db.client.auth.sign_out()
    st.session_state.authenticated = False
    st.session_state.user = None
    st.session_state.role = None
    st.session_state.user_profile = None
    st.rerun()

def require_auth():
    """Guard clause for pages requiring auth."""
    init_auth()
    if not st.session_state.authenticated:
        login_form()
        st.stop()
