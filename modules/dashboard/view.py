import streamlit as st
from modules.dashboard.services import DashboardService

def render():
    st.header("📊 Дашборд виробництва")
    
    service = DashboardService()
    stats = service.get_stats()
    
    if "error" in stats:
        st.error(f"Помилка завантаження даних: {stats['error']}")
    
    # Metrics Row
    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.metric("📦 Всього замовлень", stats["total_orders"])
        
    with c2:
        st.metric("⚙️ В роботі (етапів)", stats["active_steps"])
        
    with c3:
        st.metric("✅ Виконано етапів", stats["completed_steps"])
        
    st.divider()
    
    st.subheader("Швидкій огляд")
    st.info("Ласкаво просимо до системи планування виробництва. Використовуйте меню зліва для навігації.")
