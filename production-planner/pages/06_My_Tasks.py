import streamlit as st
import pandas as pd
from modules.orders.services import OrderService
from ui.components import load_custom_css, render_task_card, render_status_badge

st.set_page_config(page_title="My Tasks", page_icon="👷", layout="wide")
load_custom_css()

st.title("👷 Операторський Пульт")

order_service = OrderService()

# 1. Login / Select Worker
workers = order_service.get_all_workers()
worker_options = {w['id']: w['full_name'] for w in workers}

col_auth, col_export = st.columns([3, 1])
with col_auth:
    selected_worker_id = st.selectbox("👤 Хто ви?", options=list(worker_options.keys()), format_func=lambda x: worker_options[x], key="worker_select")

if selected_worker_id:
    # 2. Fetch Tasks
    tasks = order_service.get_worker_tasks(selected_worker_id)
    
    if tasks:
        # Separate filtered lists
        active_tasks = [t for t in tasks if t.get('status') == 'in_progress']
        pending_tasks = [t for t in tasks if t.get('status') == 'not_started' or t.get('status') == 'paused']
        done_tasks = [t for t in tasks if t.get('status') == 'done']
        
        # Tabs for better focus
        tab_active, tab_pending, tab_done = st.tabs([
            f"🔥 В роботі ({len(active_tasks)})", 
            f"📋 Черга ({len(pending_tasks)})", 
            f"✅ Виконано ({len(done_tasks)})"
        ])
        
        # --- ACTIVE TASKS ---
        with tab_active:
            if not active_tasks:
                st.info("Немає активних завдань. Візьміть щось із черги!")
            for t in active_tasks:
                with st.container():
                    render_task_card(t)
                    c1, c2 = st.columns(2)
                    if c1.button("✅ ЗАВЕРШИТИ", key=f"finish_{t['id']}", type="primary", use_container_width=True):
                         order_service.update_operation_status(t['id'], 'done', quantity_done=t['quantity'])
                         st.rerun()
                    if c2.button("⏸️ ПАУЗА", key=f"pause_{t['id']}", use_container_width=True):
                         order_service.update_operation_status(t['id'], 'paused')
                         st.rerun()
                    st.divider()

        # --- PENDING TASKS ---
        with tab_pending:
            if not pending_tasks:
                st.success("Черга пуста!")
            for t in pending_tasks:
                with st.container():
                    render_task_card(t)
                    if st.button("▶️ ПОЧАТИ РОБОТУ", key=f"start_{t['id']}", type="primary", use_container_width=True):
                         order_service.update_operation_status(t['id'], 'in_progress')
                         st.rerun()
                    st.divider()

        # --- DONE TASKS ---
        with tab_done:
            for t in done_tasks:
                render_task_card(t)
                st.caption(f"Completed at: {t.get('updated_at')}")
                st.divider()

        # --- EXPORT ---
        with col_export:
            # Excel Export logic (kept simple)
            try:
                # Flat map for CSV
                csv_data = []
                for t in tasks:
                    csv_data.append({
                        "Order": t.get('orders', {}).get('order_number'),
                        "Product": t.get('orders', {}).get('product_name'),
                        "Operation": t.get('operations_catalog', {}).get('operation_key'),
                        "Status": t.get('status'),
                        "Quantity": t.get('quantity')
                    })
                df_csv = pd.DataFrame(csv_data)
                csv = df_csv.to_csv(index=False).encode('utf-8')
                st.download_button(
                    "💾 Excel/CSV",
                    csv,
                    "tasks.csv",
                    "text/csv",
                    key='download-csv'
                )
            except Exception:
                pass

    else:
        st.info("🎉 У вас немає призначених завдань! Відпочивайте.")
else:
    st.info("⬅️ Будь ласка, оберіть своє ім'я.")
