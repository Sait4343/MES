import streamlit as st
import pandas as pd
from datetime import datetime
from modules.orders.services import OrderService

st.set_page_config(page_title="My Tasks", page_icon="👷", layout="wide")

st.title("👷 Мої Завдання (My Tasks)")

order_service = OrderService()

# 1. Login / Select Worker
# In a real app, this would be auto-detected from login.
# Here we simulate it with a dropdown.
workers = order_service.get_all_workers()
worker_options = {w['id']: w['full_name'] for w in workers}

selected_worker_id = st.selectbox("👤 Хто ви?", options=list(worker_options.keys()), format_func=lambda x: worker_options[x], key="worker_select")

if selected_worker_id:
    # 2. Fetch Tasks
    tasks = order_service.get_worker_tasks(selected_worker_id)
    
    if tasks:
        # Prepare Data for Display
        task_data = []
        for t in tasks:
            order_info = t.get('orders', {})
            op_info = t.get('operations_catalog', {})
            
            task_data.append({
                'ID': t['id'],
                'Order': order_info.get('order_number', 'N/A'),
                'Article': order_info.get('article', 'N/A'),
                'Operation': op_info.get('operation_key', 'Unknown'),
                'Start': t.get('scheduled_start_at'),
                'Status': t.get('status', 'not_started'),
                'Qty': t.get('quantity', 0),
                'Done': t.get('completed_quantity', 0),
                'Planned Start': t.get('scheduled_start_at', '').replace('T', ' ')[:16]
            })
            
        df_tasks = pd.DataFrame(task_data)
        
        # --- EXPORT BUTTON ---
        with st.sidebar:
            st.markdown("### 📥 Офлайн")
            
            # Excel Export
            try:
                # Convert to CSV for simplicity and compatibility
                csv = df_tasks.to_csv(index=False).encode('utf-8')
                st.download_button(
                    "💾 Завантажити Excel/CSV",
                    csv,
                    "my_tasks.csv",
                    "text/csv",
                    key='download-csv'
                )
            except Exception as e:
                st.error(f"Export error: {e}")
                
            st.info("Tip: Щоб роздрукувати завдання, натисніть Ctrl+P.")

        # --- TASK LIST (Card View) ---
        st.markdown(f"### 📋 Завдання для {worker_options[selected_worker_id]}")
        
        status_colors = {
            'not_started': 'grey',
            'in_progress': 'blue',
            'done': 'green',
            'paused': 'orange'
        }
        
        for index, row in df_tasks.iterrows():
            # Card Styling
            status_color = status_colors.get(row['Status'], 'grey')
            
            with st.container(border=True):
                col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
                
                with col1:
                    st.markdown(f"**{row['Order']}** | {row['Article']}")
                    st.caption(f"🔹 {row['Operation']}")
                
                with col2:
                    st.markdown(f"📅 **{row['Planned Start']}**")
                    st.markdown(f"📦 {row['Done']} / {row['Qty']}")
                
                with col3:
                   st.markdown(f":{status_color}[**{row['Status'].upper().replace('_', ' ')}**]")
                
                with col4:
                    # Action Buttons
                    if row['Status'] == 'not_started':
                        if st.button("▶️ ПОЧАТИ", key=f"start_{row['ID']}"):
                            order_service.update_operation_status(row['ID'], 'in_progress')
                            st.rerun()
                    elif row['Status'] == 'in_progress':
                        if st.button("✅ ЗАВЕРШИТИ", key=f"finish_{row['ID']}"):
                            order_service.update_operation_status(row['ID'], 'done', quantity_done=row['Qty'])
                            st.rerun()
                        if st.button("⏸️ ПАУЗА", key=f"pause_{row['ID']}"):
                            order_service.update_operation_status(row['ID'], 'paused')
                            st.rerun()
                    elif row['Status'] == 'paused':
                         if st.button("▶️ ПРОДОВЖИТИ", key=f"resume_{row['ID']}"):
                            order_service.update_operation_status(row['ID'], 'in_progress')
                            st.rerun()
            
    else:
        st.info("🎉 У вас немає активних завдань! Відпочивайте.")
else:
    st.info("⬅️ Будь ласка, оберіть своє ім'я зі списку зліва (або зверху).")
