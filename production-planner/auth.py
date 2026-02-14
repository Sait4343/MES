import streamlit as st
from utils import supabase
import time

def login():
    """Handle user login."""
    st.subheader("Login")
    
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    
    if st.button("Log In"):
        if not email or not password:
            st.warning("Please enter both email and password")
            return
            
        try:
            with st.spinner("Logging in..."):
                response = supabase.auth.sign_in_with_password({
                    "email": email,
                    "password": password
                })
                
                # Verify session
                session = response.session
                if session:
                    st.session_state["user"] = session.user
                    st.session_state["access_token"] = session.access_token
                    st.session_state["role"] = get_current_user_role(session.user.id)
                    st.success("Logged in successfully!")
                    time.sleep(1)
                    st.rerun()
        except Exception as e:
            st.error(f"Login failed: {e}")

def logout():
    """Handle user logout."""
    try:
        supabase.auth.sign_out()
        st.session_state.clear()
        st.rerun()
    except Exception as e:
        st.error(f"Logout failed: {e}")

def get_current_user_role(user_id: str):
    """Fetch the role of the current user."""
    try:
        response = supabase.table("profiles").select("role").eq("id", user_id).single().execute()
        if response.data:
            return response.data['role']
        return "worker" # Default fallback
    except Exception as e:
        st.error(f"Error fetching user role: {e}")
        return "worker"

def check_auth():
    """Check if user is authenticated and return user object."""
    if "user" not in st.session_state:
        return None
    return st.session_state["user"]

def require_auth():
    """Stop execution if user is not authenticated."""
    user = check_auth()
    if not user:
        login()
        st.stop()
    return user

def require_role(allowed_roles: list):
    """Ensure user has one of the allowed roles."""
    user = require_auth()
    role = st.session_state.get("role", "worker")
    
    if role not in allowed_roles:
        st.error("You do not have permission to access this page.")
        st.stop()
