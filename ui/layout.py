import streamlit as st
from core.config import AppConfig, ROLE_LABELS, UserRole
from core import auth

def render_sidebar():
    """Render the sidebar navigation."""
    # --- Role Switcher (Added) ---
    st.sidebar.markdown("### 🎭 Role Switcher (Sim)")
    sim_role = st.sidebar.selectbox(
        "Perspective", 
        ["Admin", "Planner", "Worker"],
        index=0,
        key="role_switcher"
    )
    
    # Map Simulation to UserRole
    role_map = {
        "Admin": UserRole.ADMIN,
        "Planner": UserRole.MANAGER,
        "Worker": UserRole.WORKER
    }
    effective_role = role_map.get(sim_role, UserRole.VIEWER)

    # Use effective_role for logic
    user_role = effective_role 

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
