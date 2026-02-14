import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.figure_factory as ff
from modules.orders.services import OrderService
from core.auth import require_auth
import datetime

# Page Config
st.set_page_config(page_title="Деталі замовлення", layout="wide", page_icon="📋")
require_auth()

def render_gantt_chart(df):
    """Render interactive Gantt chart using Plotly."""
    if df.empty or 'scheduled_start_at' not in df.columns or 'scheduled_end_at' not in df.columns:
        st.warning("Немає запланованих операцій з датами для відображення діаграми Ганта.")
        return

    # Filter only valid dates
    gantt_data = df.dropna(subset=['scheduled_start_at', 'scheduled_end_at']).copy()
    
    if gantt_data.empty:
        st.info("Додайте дати початку та завершення до операцій, щоб побачити діаграму.")
        return

    # Ensure datetime format
    gantt_data['Start'] = pd.to_datetime(gantt_data['scheduled_start_at'])
    gantt_data['Finish'] = pd.to_datetime(gantt_data['scheduled_end_at'])
    gantt_data['Task'] = gantt_data['operation_name']
    gantt_data['Resource'] = gantt_data['section_name']  # Color by Section

    fig = px.timeline(
        gantt_data, 
        x_start="Start", 
        x_end="Finish", 
        y="Task", 
        color="Resource",
        hover_data=["worker_name", "status", "quantity"],
        title="Графік виконання замовлення"
    )
    fig.update_yaxes(autorange="reversed") # Should match logical order
    fig.update_layout(xaxis_title="Час", yaxis_title="Операція")
    
    st.plotly_chart(fig, use_container_width=True)

def main():
    service = OrderService()
    
    # 1. Check for selected order in session state
    if 'selected_order_id' not in st.session_state:
        st.warning("Будь ласка, оберіть замовлення на сторінці 'Замовлення'.")
        if st.button("⬅️ До списку замовлень"):
            st.switch_page("pages/01_Orders.py")
        return

    order_id = st.session_state.selected_order_id
    order = service.get_order_by_id(order_id)
    
    if not order:
        st.error("Замовлення не знайдено.")
        if st.button("⬅️ Повернутися"):
            st.switch_page("pages/01_Orders.py")
        return

    # --- Header ---
    col_back, col_title = st.columns([1, 10])
    with col_back:
        if st.button("⬅️", help="Назад до списку"):
            del st.session_state.selected_order_id
            st.switch_page("pages/01_Orders.py")
    with col_title:
        st.title(f"Деталі замовлення: {order['order_number']}")

    # --- Info Blocks ---
    i1, i2, i3, i4 = st.columns(4)
    i1.metric("Виріб", order['product_name'])
    i2.metric("Кількість", order['quantity'])
    i3.metric("Контрагент", order.get('contractor') or "-")
    i4.metric("Статус", "В роботі") # Placeholder for logic

    st.divider()

    # --- Fetch Operations Data ---
    ops_data = service.get_order_operations(order_id)
    
    if not ops_data:
        st.info("Для цього замовлення ще не створено детального плану операцій.")
        # TODO: Add button to "Generate Default Plan" if needed
    else:
        # Pre-process data for easy display
        rows = []
        for op in ops_data:
            sec = op.get('sections')
            work = op.get('profiles')
            rows.append({
                'id': op['id'],
                'operation_name': op['operation_name'],
                'section_name': sec['name'] if sec else 'Не призначено',
                'worker_name': work['full_name'] if work else 'Не призначено',
                'quantity': op['quantity'],
                'status': op['status'],
                'scheduled_start_at': op.get('scheduled_start_at'),
                'scheduled_end_at': op.get('scheduled_end_at'),
                'sort_order': op['sort_order']
            })
        
        df_ops = pd.DataFrame(rows)

        # --- TABS ---
        tab_gantt, tab_list, tab_daily, tab_resources = st.tabs([
            "📅 Діаграма Ганта", 
            "📋 Список операцій", 
            "📆 Розклад по днях", 
            "👥 Завантаження"
        ])

        # 1. GANTT CHART
        with tab_gantt:
            render_gantt_chart(df_ops)

        # 2. OPERATIONS LIST
        with tab_list:
            st.dataframe(
                df_ops,
                column_config={
                    "operation_name": "Операція",
                    "section_name": "Дільниця",
                    "worker_name": "Працівник",
                    "quantity": "К-ть",
                    "status": "Статус",
                    "scheduled_start_at": st.column_config.DatetimeColumn("Початок", format="MM-DD HH:mm"),
                    "scheduled_end_at": st.column_config.DatetimeColumn("Кінець", format="MM-DD HH:mm")
                },
                column_order=["operation_name", "section_name", "worker_name", "quantity", "scheduled_start_at", "scheduled_end_at", "status"],
                hide_index=True,
                use_container_width=True
            )

        # 3. DAILY SCHEDULE
        with tab_daily:
            if 'scheduled_start_at' in df_ops.columns:
                df_daily = df_ops.copy()
                df_daily['date'] = pd.to_datetime(df_daily['scheduled_start_at']).dt.date
                
                # Group by Date
                unique_dates = sorted(df_daily['date'].dropna().unique())
                
                for d in unique_dates:
                    with st.expander(f"📆 {d.strftime('%Y-%m-%d')}", expanded=True):
                        day_ops = df_daily[df_daily['date'] == d]
                        st.dataframe(
                            day_ops[['operation_name', 'section_name', 'worker_name', 'scheduled_start_at', 'scheduled_end_at']],
                            hide_index=True,
                            use_container_width=True
                        )
            else:
                st.info("Немає даних з датами.")

        # 4. RESOURCE BREAKDOWN
        with tab_resources:
            r1, r2 = st.columns(2)
            
            with r1:
                st.subheader("По дільницях")
                sec_counts = df_ops['section_name'].value_counts().reset_index()
                sec_counts.columns = ['Дільниця', 'Кількість операцій']
                st.dataframe(sec_counts, hide_index=True, use_container_width=True)
                
                # Simple Bar Chart
                st.bar_chart(sec_counts.set_index('Дільниця'))

            with r2:
                st.subheader("По працівниках")
                work_counts = df_ops['worker_name'].value_counts().reset_index()
                work_counts.columns = ['Працівник', 'Кількість операцій']
                st.dataframe(work_counts, hide_index=True, use_container_width=True)

if __name__ == "__main__":
    main()
