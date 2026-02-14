import streamlit as st
import plotly.express as px
import pandas as pd
from modules.dashboard.services import DashboardService
from modules.analytics.services import AnalyticsService
import io

def render():
    st.header("📊 Дашборд виробництва")
    
    # Services
    dash_service = DashboardService()
    analytics_service = AnalyticsService()
    
    # 1. High Level Stats
    stats = dash_service.get_stats()
    c1, c2, c3 = st.columns(3)
    c1.metric("📦 Всього замовлень", stats.get("total_orders", 0))
    c2.metric("⚙️ В роботі (етапів)", stats.get("active_steps", 0))
    c3.metric("✅ Виконано етапів", stats.get("completed_steps", 0))
    
    st.divider()
    
    # 2. Planning & Scheduling
    st.subheader("📅 Графік виробництва та Навантаження")
    
    df_plan = analytics_service.get_planning_data()
    
    if df_plan.empty:
        st.info("Немає спланованих операцій для відображення графіку.")
    else:
        # A. Gantt Chart
        st.write("##### 🗓️ Діаграма Ганта (Замовлення)")
        
        # Ensure we have datetime
        if 'start_time' in df_plan.columns and 'end_time' in df_plan.columns:
            fig_gantt = px.timeline(
                df_plan, 
                x_start="start_time", 
                x_end="end_time", 
                y="Order",
                color="Section",
                hover_data=["operation_name", "Worker", "total_estimated_time"],
                title="Графік виконання замовлень"
            )
            fig_gantt.update_yaxes(autorange="reversed")
            st.plotly_chart(fig_gantt, use_container_width=True)
            
        # B. Workload Analysis
        st.divider()
        c_load1, c_load2 = st.columns(2)
        
        with c_load1:
            st.write("##### 🏭 Навантаження на Дільниці")
            # Group by Section -> Sum(total_estimated_time)
            section_load = df_plan.groupby('Section')['total_estimated_time'].sum().reset_index()
            # Merge with capacity? df_plan has 'Section Cap' repeated.
            # Let's exclude duplicates.
            sec_caps = df_plan[['Section', 'Section Cap']].drop_duplicates()
            
            merged_sec = pd.merge(section_load, sec_caps, on="Section")
            merged_sec['Idle Capacity'] = merged_sec['Section Cap'] - merged_sec['total_estimated_time']
            
            # Simple Bar
            fig_sec = px.bar(
                merged_sec, 
                x="Section", 
                y=["total_estimated_time", "Idle Capacity"],
                title="Навантаження vs Потужність (хв)",
                labels={"value": "Хвилини", "variable": "Тип"}
            )
            st.plotly_chart(fig_sec, use_container_width=True)
            
        with c_load2:
            st.write("##### 👷 Навантаження на Працівників")
            worker_load = df_plan[df_plan['Worker'] != 'Unassigned'].groupby('Worker')['total_estimated_time'].sum().reset_index()
            fig_work = px.bar(worker_load, x="Worker", y="total_estimated_time", title="Зайнятість працівників (хв)")
            st.plotly_chart(fig_work, use_container_width=True)
            
        # C. Export Schedule
        st.divider()
        if st.button("📥 Завантажити повний план-графік (Excel)"):
            # Prepare Export
            export_df = df_plan[[
                "planned_date", "Order", "Product", "Section", 
                "operation_name", "quantity", "norm_time_per_unit", 
                "total_estimated_time", "start_time", "end_time", "Worker", "status"
            ]].copy()
            
            # Format dates
            export_df['start_time'] = export_df['start_time'].dt.strftime('%Y-%m-%d %H:%M')
            export_df['end_time'] = export_df['end_time'].dt.strftime('%Y-%m-%d %H:%M')
            
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer) as writer:
                export_df.to_excel(writer, index=False, sheet_name="Schedule")
                
                # Add analytics sheets
                section_load.to_excel(writer, index=False, sheet_name="Section Load")
                worker_load.to_excel(writer, index=False, sheet_name="Worker Load")
                
            st.download_button(
                label="Зберегти файл",
                data=buffer.getvalue(),
                file_name="production_schedule_full.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

