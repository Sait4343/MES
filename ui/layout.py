import streamlit as st
from core.config import AppConfig, ROLE_LABELS, UserRole
from core import auth

def render_sidebar():
    """Render the sidebar navigation."""
    st.sidebar.title(f"🏭 {AppConfig.APP_NAME}")
    
    user_role = st.session_state.get("role", UserRole.VIEWER)

    # User Info
    if st.session_state.user_profile:
        full_name = st.session_state.user_profile.get("full_name", "User")
        st.sidebar.markdown(f"**{full_name}**")
        st.sidebar.caption(f"Роль: {ROLE_LABELS.get(user_role, user_role)}")
        st.sidebar.divider()

    # Navigation Menu
    # Base Menu (All Users)
    menu_options = {
        "dashboard": "📊 Дашборд",
        "planning": "📅 Планування",
        "orders": "📦 Замовлення",
        "inventory": "📦 Склад",
        # "calendar": "🗓️ Календар", # Only if module exists and is desired for all
        "calendar": "🗓️ Календар",
        "settings": "⚙️ Налаштування",
    }
    
    # Restricted Pages
    if user_role in [UserRole.ADMIN, UserRole.MANAGER]:
         menu_options["workers"] = "👥 Працівники"
         menu_options["operations"] = "🧵 Операції"  # Added Operations
         menu_options["analytics"] = "📈 Аналітика"

    # Worker/Viewer see base menu + above conditions
    # Worker/Viewer do NOT see Analytics or Workers in this design
    
    # Simple navigation
    selection = st.sidebar.radio("Меню", list(menu_options.keys()), format_func=lambda x: menu_options[x], label_visibility="collapsed")
    
    st.sidebar.divider()
    if st.sidebar.button("Вийти"):
        auth.logout()

    return selection
