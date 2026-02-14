import streamlit as st
import pandas as pd
import plotly.express as px
from modules.analytics.services import AnalyticsService

def render():
    st.header("📈 Розширена Аналітика")
    
    service = AnalyticsService()
    
    # 1. Filters (Dates could be added here)
    # c1, c2 = st.columns(2)
    # with c1:
    #     date_range = st.date_input("Період", [])
    
    if st.button("🔄 Оновити дані"):
        st.cache_data.clear()
    
    orders_df, steps_df, profiles_df = service.get_raw_data()
    
    if orders_df.empty:
        st.info("Недостатньо даних для аналізу.")
        return

    # --- KPIs ---
    kpis = service.calculate_kpis(orders_df, steps_df)
    
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Всього замовлень", kpis['total'])
    k2.metric("OTD (Вчасно)", f"{kpis['otd']}%")
    k3.metric("Затримки", kpis['delays'], delta=-kpis['delays'], delta_color="inverse")
    # Efficiency proxy: tasks completed / total steps
    total_steps = len(steps_df)
    done_steps = len(steps_df[steps_df['status'] == 'done']) if not steps_df.empty else 0
    progress = int((done_steps / total_steps * 100) if total_steps > 0 else 0)
    k4.metric("Загальний прогрес", f"{progress}%")
    
    st.divider()
    
    tab1, tab2, tab3 = st.tabs(["🏭 Виробництво", "👥 Ефективність", "📉 Вузькі місця"])
    
    with tab1:
        st.subheader("Статус виробництва")
        status_df = service.get_step_status_dist(steps_df)
        if not status_df.empty:
            # Altair/Streamlit generic chart or Plotly
            # Using st.bar_chart for simplicity or Plotly for nicer UI
            fig = px.pie(status_df, values='count', names='status', title='Розподіл статусів етапів', hole=0.4)
            st.plotly_chart(fig, use_container_width=True)
            
    with tab2:
        st.subheader("Продуктивність працівників")
        worker_perf = service.get_worker_performance(steps_df, profiles_df)
        if not worker_perf.empty:
            fig = px.bar(worker_perf, x='Worker', y='Completed Tasks', title='Виконані завдання за працівником', color='Completed Tasks')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Немає даних про виконані завдання.")
            
    with tab3:
        st.subheader("Аналіз вузьких місць (Середня тривалість)")
        bottlenecks = service.get_bottlenecks(steps_df)
        if not bottlenecks.empty:
            fig = px.bar(bottlenecks, x='Step', y='Avg Duration (Hours)', title='Середній час на етап (години)', color='Avg Duration (Hours)', color_continuous_scale='RdYlGn_r')
            st.plotly_chart(fig, use_container_width=True)
            st.caption("Чим вищий стовпчик, тим більше часу займає етап в середньому.")
        else:
            st.info("Немає даних про тривалість (потрібні Start/Finish times).")

    # Export
    st.divider()
    # Prepare export info
    if st.button("📥 Експортувати звіт (CSV)"):
        # Simple export of aggregated data
        csv = orders_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            "Завантажити Orders.csv",
            csv,
            "orders_analytics.csv",
            "text/csv",
            key='download-csv'
        )
