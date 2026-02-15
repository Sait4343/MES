import streamlit as st
from core.config import AppConfig, ROLE_LABELS, UserRole
from core import auth

def render_sidebar():
    """Render the sidebar navigation."""
    # --- Role Switcher (Buttons) ---
    st.sidebar.markdown("### 🎭 Change Role")
    r_col1, r_col2, r_col3 = st.sidebar.columns(3)
    
    if r_col1.button("👮 Admin"):
        st.session_state["role"] = UserRole.ADMIN
        st.rerun()
    if r_col2.button("📅 Planner"):
        st.session_state["role"] = UserRole.MANAGER
        st.rerun()
    if r_col3.button("👷 Worker"):
        st.session_state["role"] = UserRole.WORKER
        st.rerun()

    # Use session state role
    user_role = st.session_state.get("role", UserRole.VIEWER) 

    # User Info
    if st.session_state.user_profile:
        full_name = st.session_state.user_profile.get("full_name", "User")
        st.sidebar.markdown(f"**{full_name}**")
        st.sidebar.caption(f"Роль: {ROLE_LABELS.get(user_role, user_role)}")
        st.sidebar.divider()

    # Navigation Menu
    # Base Menu
    menu_options = {
        "dashboard": "📊 Дашборд",
    }
    
    if user_role in [UserRole.ADMIN, UserRole.MANAGER]:
         menu_options["planning"] = "📅 Планування"
         menu_options["orders"] = "📦 Замовлення"
         menu_options["inventory"] = "📦 Склад"
         menu_options["calendar"] = "🗓️ Календар"
         menu_options["settings"] = "⚙️ Налаштування"
         
         # Restricted Pages
         menu_options["workers"] = "👥 Працівники"
         menu_options["operations"] = "🧵 Операції"
         menu_options["sections"] = "🏭 Дільниці"
         menu_options["analytics"] = "📈 Аналітика"
         
         # New pages support
         menu_options["quality"] = "🔍 Якість"
         menu_options["maintenance"] = "🛠️ Обслуговування"

    if user_role == UserRole.WORKER or user_role == UserRole.ADMIN:
        # Worker sees My Tasks
        menu_options["my_tasks"] = "🔨 Мої завдання (My Tasks)"
    
    # Simple navigation
    selection = st.sidebar.radio("Меню", list(menu_options.keys()), format_func=lambda x: menu_options[x], label_visibility="collapsed")
    
    st.sidebar.divider()
    if st.sidebar.button("Вийти"):
        auth.logout()

    return selection
