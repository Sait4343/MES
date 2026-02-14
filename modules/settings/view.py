import streamlit as st
from core.config import ROLE_LABELS, UserRole

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

    # --- Admin Section: User Management ---
    if st.session_state.role == UserRole.ADMIN:
        st.divider()
        st.subheader("👥 Керування користувачами (Адмін)")
        
        from modules.workers.services import WorkerService
        worker_service = WorkerService()
        workers = worker_service.get_all_workers()
        
        if workers:
            st.info("Тут ви можете змінювати ролі користувачів. Нові користувачі повинні зареєструватись самостійно, після чого ви зможете надати їм права.")
            
            for w in workers:
                with st.expander(f"{w.get('full_name', 'Unknown')} ({w.get('email')})"):
                    c1, c2 = st.columns([2, 1])
                    c1.write(f"**Email:** {w.get('email')}")
                    c1.write(f"**ID:** `{w.get('id')}`")
                    
                    # Edit Full Name
                    new_name = c1.text_input("Повне ім'я", value=w.get('full_name', ''), key=f"name_{w['id']}")
                    
                    # Edit Role
                    current_role = w.get('role', 'worker')
                    new_role = c2.selectbox(
                        "Роль", 
                        options=[UserRole.ADMIN, UserRole.MANAGER, UserRole.WORKER, UserRole.VIEWER],
                        index=[UserRole.ADMIN, UserRole.MANAGER, UserRole.WORKER, UserRole.VIEWER].index(current_role) if current_role in [UserRole.ADMIN, UserRole.MANAGER, UserRole.WORKER, UserRole.VIEWER] else 2,
                        key=f"st_role_{w['id']}",
                        format_func=lambda x: ROLE_LABELS.get(x, x)
                    )
                    
                    if c2.button("Зберегти зміни", key=f"btn_save_{w['id']}"):
                        updates = {}
                        if new_role != current_role:
                            updates["role"] = new_role
                        if new_name != w.get('full_name'):
                            updates["full_name"] = new_name
                            
                        if updates:
                            # We can use update_worker_profile for name and update_worker_role for role, 
                            # or just update_worker_profile if it handles role too?
                            # service.update_worker_profile handles generic data.
                            # But role might need special handling if we separated it?
                            # In step 433, update_worker_profile is generic table update.
                            # update_worker_role is also generic table update.
                            # So update_worker_profile works for both.
                            
                            worker_service.update_worker_profile(w['id'], updates)
                            st.success(f"Дані оновлено!")
                            st.rerun()
                        else:
                            st.info("Змін не виявлено.")
