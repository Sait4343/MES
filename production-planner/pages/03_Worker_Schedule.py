import streamlit as st
import pandas as pd
import plotly.express as px
from core.database import DatabaseService
from core.auth import require_auth
import datetime

st.set_page_config(page_title="Графік працівників", layout="wide", page_icon="📅")
require_auth()

def fetch_worker_schedule(worker_id):
    """Fetch assigned operations for a worker."""
    db = DatabaseService()
    try:
        # Join with orders to get Order Number
        return db.client.table("order_operations").select(
            "*, orders(order_number), sections(name)"
        ).eq("assigned_worker_id", worker_id).execute().data
    except Exception as e:
        st.error(f"Error fetching schedule: {e}")
        return []

def fetch_all_workers():
    db = DatabaseService()
    try:
        return db.client.table("profiles").select("id, full_name, role").eq("role", "worker").execute().data
    except:
        return []

def main():
    st.title("📅 Графік роботи працівників")
    
    # 1. Select Worker
    workers = fetch_all_workers()
    if not workers:
        st.info("Немає працівників у системі.")
        return

    worker_dict = {w['id']: w['full_name'] for w in workers}
    
    # Layout: Sidebar for selection
    with st.sidebar:
        st.header("Налаштування")
        selected_worker_id = st.selectbox("Оберіть працівника", options=list(worker_dict.keys()), format_func=lambda x: worker_dict[x])
        
        view_mode = st.radio("Режим перегляду", ["День", "Тиждень", "Місяць"])

    if selected_worker_id:
        worker_name = worker_dict[selected_worker_id]
        st.subheader(f"Розклад: {worker_name}")
        
        schedule_data = fetch_worker_schedule(selected_worker_id)
        
        if not schedule_data:
            st.info("У цього працівника немає призначених завдань.")
        else:
            # Process Data
            rows = []
            for item in schedule_data:
                rows.append({
                    "Task": item.get('operation_name'),
                    "Order": item.get('orders')['order_number'] if item.get('orders') else "-",
                    "Section": item.get('sections')['name'] if item.get('sections') else "-",
                    "Start": item.get('scheduled_start_at'),
                    "Finish": item.get('scheduled_end_at'),
                    "Status": item.get('status'),
                    "Quantity": item.get('quantity')
                })
            
            df = pd.DataFrame(rows)
            
            # Filter valid dates for Gantt
            df_gantt = df.dropna(subset=['Start', 'Finish']).copy()
            
            if not df_gantt.empty:
                # Convert to datetime
                df_gantt['Start'] = pd.to_datetime(df_gantt['Start'])
                df_gantt['Finish'] = pd.to_datetime(df_gantt['Finish'])

                # GANTT CHART
                fig = px.timeline(
                    df_gantt, 
                    x_start="Start", 
                    x_end="Finish", 
                    y="Order", 
                    color="Status",
                    hover_data=["Task", "Section", "Quantity"],
                    title=f"Завантаження: {worker_name}"
                )
                fig.update_yaxes(autorange="reversed")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Завдання є, але не вказано час виконання (Start/End).")

            # TABLE VIEW
            st.subheader("📋 Детальний список завдань")
            st.dataframe(
                df, 
                column_config={
                    "Start": st.column_config.DatetimeColumn("Початок", format="YYYY-MM-DD HH:mm"),
                    "Finish": st.column_config.DatetimeColumn("Кінець", format="YYYY-MM-DD HH:mm")
                },
                use_container_width=True
            )

if __name__ == "__main__":
    main()
