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
            
        # B. Section Analytics
        st.divider()
        st.subheader("🏭 Аналітика по Дільницях")
        
        # Get section metrics
        section_metrics = analytics_service.get_section_metrics_summary()
        
        if not section_metrics:
            st.info("Немає даних по дільницях.")
        else:
            # Display section cards in grid
            num_cols = 3
            cols = st.columns(num_cols)
            
            for idx, metric in enumerate(section_metrics):
                col_idx = idx % num_cols
                
                with cols[col_idx]:
                    with st.container(border=True):
                        st.markdown(f"### {metric['section_name']}")
                        
                        # Metrics row
                        m1, m2 = st.columns(2)
                        
                        capacity_hours = metric['capacity_minutes'] / 60
                        scheduled_hours = metric['scheduled_minutes'] / 60
                        
                        m1.metric(
                            "Завантаження", 
                            f"{scheduled_hours:.1f}/{capacity_hours:.0f} год",
                            delta=f"{metric['utilization_percent']}%"
                        )
                        m2.metric("Операції сьогодні", metric['num_operations'])
                        
                        # Gauge chart for utilization
                        utilization = metric['utilization_percent']
                        
                        # Determine color based on utilization
                        if utilization < 70:
                            color = "green"
                        elif utilization < 90:
                            color = "orange"
                        else:
                            color = "red"
                        
                        fig_gauge = px.pie(
                            values=[utilization, 100 - utilization],
                            names=['Використано', 'Вільно'],
                            hole=0.7,
                            color_discrete_sequence=[color, '#e0e0e0']
                        )
                        fig_gauge.update_traces(textinfo='none', hoverinfo='label+percent')
                        fig_gauge.update_layout(
                            showlegend=False,
                            height=150,
                            margin=dict(t=0, b=0, l=0, r=0),
                            annotations=[dict(text=f'{utilization}%', x=0.5, y=0.5, font_size=20, showarrow=False)]
                        )
                        st.plotly_chart(fig_gauge, use_container_width=True, key=f"gauge_{metric['section_id']}")
                        
                        # Weekly trend mini chart
                        trend_df = analytics_service.get_section_weekly_trend(metric['section_id'], num_days=7)
                        
                        if not trend_df.empty:
                            fig_trend = px.bar(
                                trend_df,
                                x='date',
                                y='utilization_percent',
                                title="Тиждень (прогноз)",
                                labels={'date': 'Дата', 'utilization_percent': '%'}
                            )
                            fig_trend.update_layout(
                                height=150,
                                margin=dict(t=30, b=20, l=20, r=20),
                                showlegend=False
                            )
                            fig_trend.update_xaxes(tickformat='%d.%m')
                            st.plotly_chart(fig_trend, use_container_width=True, key=f"trend_{metric['section_id']}")
                        
                        # Expandable details
                        with st.expander("📊 Детальна інформація"):
                            st.write(f"**Потужність:** {capacity_hours:.1f} год/день")
                            st.write(f"**Заплановано:** {scheduled_hours:.1f} год")
                            st.write(f"**Працівників:** {metric['num_workers']}")
                            st.write(f"**Вільно:** {(capacity_hours - scheduled_hours):.1f} год")
            
            # C. Worker Workload (keep existing)
            st.divider()
            st.write("##### 👷 Навантаження на Працівників")
            worker_load = df_plan[df_plan['Worker'] != 'Unassigned'].groupby('Worker')['total_estimated_time'].sum().reset_index()
            if not worker_load.empty:
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

