import sys
import os

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

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
    
    st.divider()
    st.subheader("🛠️ Планування виробництва (Маршрут)")
    
    with st.container(border=True):
        # 1. Initialize Planning Session
        all_sections = sections_service.get_all_sections()
        if all_sections.empty:
            st.error("Спочатку створіть Дільниці.")
        else:
            sec_dict = {s['id']: s['name'] for s in all_sections.to_dict('records')}
            
            # MULTI-SELECT Sections
            selected_section_ids = st.multiselect(
                "1. Оберіть дільниці, які будуть задіяні:",
                options=list(sec_dict.keys()),
                format_func=lambda x: sec_dict[x]
            )
            
            if selected_section_ids:
                st.write("---")
                st.write("##### Додавання операцій по дільницях:")
                
                # Fetch Catalog once
                all_ops = service.get_available_operations()
                
                for sec_id in selected_section_ids:
                    sec_name = sec_dict[sec_id]
                    with st.expander(f"📍 Дільниця: {sec_name}", expanded=True):
                        # Filter ops for this section
                        # Assuming 'section' column in catalog maps to Section Name
                        sec_ops = [op for op in all_ops if op.get('section') == sec_name]
                        
                        if not sec_ops:
                            st.warning("Немає операцій в каталозі для цієї дільниці.")
                        else:
                            c1, c2, c3, c4 = st.columns([3, 2, 2, 1])
                            
                            with c1:
                                op_options = {op['id']: f"{op.get('operation_key')} | {op.get('article')}" for op in sec_ops}
                                sel_op_id = st.selectbox(f"Операція ({sec_name})", options=list(op_options.keys()), format_func=lambda x: op_options[x], key=f"op_{sec_id}")
                            
                            sel_op = next((op for op in sec_ops if op['id'] == sel_op_id), None)
                            
                            with c2:
                                # Workers for this section
                                workers = service.get_workers_for_section(sec_name)
                                w_opts = {w['id']: w['full_name'] for w in workers}
                                sel_worker = st.selectbox(f"Працівник ({sec_name})", options=[None]+list(w_opts.keys()), format_func=lambda x: w_opts[x] if x else "---", key=f"w_{sec_id}")
                            
                            with c3:
                                qty_val = st.number_input(f"К-ть ({sec_name})", value=order['quantity'], min_value=1, key=f"q_{sec_id}")
                            
                            with c4:
                                st.write("") # Spacer
                                st.write("")
                                if st.button("➕ Додати", key=f"btn_{sec_id}"):
                                    # Add to DB
                                    new_op = {
                                        "order_id": order_id,
                                        "section_id": sec_id,
                                        "assigned_worker_id": sel_worker,
                                        "operation_catalog_id": sel_op['id'],
                                        "operation_name": f"{sel_op.get('operation_key')} - {sel_op.get('article')}", # Snapshot
                                        "quantity": qty_val,
                                        "norm_time_per_unit": sel_op.get('norm_time', 0),
                                        # Sort order: max currently + 1? For now, 0
                                        "sort_order": len(ops_data) + 1 if ops_data else 1
                                    }
                                    res = service.create_order_operation(new_op)
                                    if res:
                                        st.success("Додано!")
                                        st.rerun()

    # AUTO-SCHEDULE BUTTON
    if ops_data: # This button should only appear if there are operations to schedule
        st.write("---")
        col_sch1, col_sch2 = st.columns([3, 1])
        with col_sch1:
            assign_w = st.checkbox("🧩 Автоматично призначити вільних працівників", value=True, help="Призначити працівників, які мають відповідну кваліфікацію та вільні у визначений час.")
        with col_sch2:
            if st.button("⚡ Авто-розклад", type="primary"):
                with st.spinner("Розрахунок графіку..."):
                    if service.auto_schedule_order(order_id, assign_workers=assign_w):
                        st.success("Графік оновлено!")
                        st.rerun()

    if ops_data: # The rest of the UI (tabs) should only appear if ops_data exists
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
                'assigned_worker_id': op.get('assigned_worker_id'), # Need for edit
                'section_id': op.get('section_id'), # Need for edit
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
            "📋 Список операцій (Редагування)", 
            "📆 Розклад по днях", 
            "👥 Завантаження"
        ])

        # 1. GANTT CHART
        with tab_gantt:
            render_gantt_chart(df_ops)

        # 2. OPERATIONS LIST
        with tab_list:
            st.info("💡 Оберіть операцію у списку, щоб змінити працівника або дати.")
            
            event = st.dataframe(
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
                use_container_width=True,
                on_select="rerun",
                selection_mode="single-row"
            )
            
            # --- EDIT FORM ---
            if event.selection.rows:
                idx = event.selection.rows[0]
                selected_row = df_ops.iloc[idx]
                
                st.divider()
                st.subheader(f"✏️ Редагування: {selected_row['operation_name']}")
                
                with st.form(key=f"edit_op_{selected_row['id']}"):
                    ec1, ec2 = st.columns(2)
                    
                    with ec1:
                        # Worker Selector using Section ID
                        sec_id = selected_row['section_id']
                        # Need section name to fetch workers? fetch_section_workers uses name.
                        # df has section_name.
                        sec_name = selected_row['section_name']
                        
                        # Fetch feasible workers
                        s_workers = service.fetch_section_workers(sec_name)
                        if not s_workers: s_workers = []
                        
                        # Create options
                        # Add current worker if not in list (might happen if rules change)
                        w_opts = {w['id']: w['full_name'] for w in s_workers}
                        
                        curr_w = selected_row['assigned_worker_id']
                        
                        new_worker = st.selectbox(
                            "Працівник", 
                            options=[None] + list(w_opts.keys()),
                            format_func=lambda x: w_opts[x] if x else "--- (Не призначено)",
                            index=([None] + list(w_opts.keys())).index(curr_w) if curr_w in w_opts else 0
                        )
                        
                    with ec2:
                        # Date Editing
                        start_v = pd.to_datetime(selected_row['scheduled_start_at']) if pd.notnull(selected_row['scheduled_start_at']) else datetime.datetime.now()
                        end_v = pd.to_datetime(selected_row['scheduled_end_at']) if pd.notnull(selected_row['scheduled_end_at']) else datetime.datetime.now()
                        
                        new_start = st.text_input("Початок (ISO)", value=start_v.isoformat())
                        new_end = st.text_input("Кінець (ISO)", value=end_v.isoformat())
                        
                    if st.form_submit_button("💾 Зберегти зміни"):
                        upd = {
                            "assigned_worker_id": new_worker,
                            "scheduled_start_at": new_start,
                            "scheduled_end_at": new_end
                        }
                        if service.update_order_operation(selected_row['id'], upd):
                            st.success("Зміни збережено!")
                            st.rerun()

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
