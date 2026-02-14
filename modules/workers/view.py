import streamlit as st
import pandas as pd
from modules.workers.services import WorkerService
from core.config import UserRole, ROLE_LABELS

def render():
    st.header("👥 Керування працівниками")
    
    # Check if current user is Admin
    current_role = st.session_state.role
    is_admin = current_role == UserRole.ADMIN
    
    if not is_admin:
        st.warning("Доступ заборонено. Тільки адміністратори можуть керувати працівниками.")
        return

    service = WorkerService()
    workers = service.get_all_workers()
    
    if not workers:
        st.info("Немає користувачів.")
        return
        
    # Stats
    total = len(workers)
    admins = sum(1 for w in workers if w['role'] == UserRole.ADMIN)
    managers = sum(1 for w in workers if w['role'] == UserRole.MANAGER)
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Всього", total)
    c2.metric("Адмінів", admins)
    c3.metric("Менеджерів", managers)
    
    st.divider()
    
    # User List
    for worker in workers:
        with st.expander(f"{worker.get('full_name', 'No Name')} ({worker.get('email')}) - {ROLE_LABELS.get(worker['role'], worker['role'])}"):
            c1, c2 = st.columns([3, 1])
            with c1:
                st.write(f"**ID:** `{worker['id']}`")
                st.write(f"**Email:** {worker['email']}")
                st.write(f"**Реєстрація:** {worker['created_at']}")
            
            with c2:
                # Role Changer
                current_worker_role = worker['role']
                options = [UserRole.ADMIN, UserRole.MANAGER, UserRole.WORKER]
                
                # Prevent changing own role effectively locks you out? No, let's allow it but warn or be careful.
                # Actually Supabase Policy might prevent self-demotion if not careful, but our policy says "Admins can update all".
                
                new_role = st.selectbox(
                    "Змінити роль", 
                    options, 
                    index=options.index(current_worker_role) if current_worker_role in options else 2,
                    key=f"role_{worker['id']}",
                    format_func=lambda x: ROLE_LABELS.get(x, x)
                )
                
                if new_role != current_worker_role:
                    if st.button("Зберегти роль", key=f"save_{worker['id']}"):
                        service.update_worker_role(worker['id'], new_role)
                        st.success("Роль оновлено!")
                        st.rerun()
