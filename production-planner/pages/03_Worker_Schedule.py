import streamlit as st
import pandas as pd
from core.database import DatabaseService
from core.auth import require_auth
import datetime

st.set_page_config(page_title="Звіти та Графіки", layout="wide", page_icon="📈")
require_auth()

def fetch_schedule_report(date_from, date_to, worker_id=None, section_id=None):
    """Fetch operations for reporting with all joined fields."""
    db = DatabaseService()
    try:
        # We need: Date (scheduled_start), Worker Name, Article, Operation, Qty, Norm, Executed
        # Join: orders(article, product_name), sections(name), profiles(full_name), operations_catalog(article, norm_time)
        
        # Note: Supabase join depth might be limited. We might need to fetch raw and merge if deep join fails.
        # Let's try deep join first.
        query = db.client.table("order_operations").select(
            "*, orders(order_number, product_name), sections(name), profiles(full_name), operations_catalog(operation_key, article, norm_time)"
        )
        
        # Date Filter
        if date_from:
            query = query.gte("scheduled_start_at", date_from.isoformat())
        if date_to:
            # Add 1 day to include end date fully or use lte
            query = query.lte("scheduled_end_at", date_to.isoformat())
            
        if worker_id:
            query = query.eq("assigned_worker_id", worker_id)
        if section_id:
            query = query.eq("section_id", section_id)
            
        return query.execute().data
    except Exception as e:
        st.error(f"Error fetching report: {e}")
        return []

def main():
    st.title("📈 Виробничі звіти та Графіки")
    
    tab_worker, tab_section = st.tabs(["👤 Денний наряд працівника", "🏭 Звіт по дільниці"])
    
    # Common Filters
    with st.sidebar:
        st.header("Фільтри")
        d_range = st.date_input("Період", [datetime.date.today(), datetime.date.today()])
        if isinstance(d_range, tuple) and len(d_range) == 2:
            start_d, end_d = d_range
        else:
            start_d = end_d = d_range if not isinstance(d_range, tuple) else d_range[0]

    # --- TAB 1: WORKER DAILY PLAN ---
    with tab_worker:
        # Worker Selector
        db = DatabaseService()
        workers = db.client.table("profiles").select("id, full_name").eq("role", "worker").execute().data
        w_map = {w['id']: w['full_name'] for w in workers}
        
        sel_workers = st.multiselect("Оберіть працівників", options=list(w_map.keys()), format_func=lambda x: w_map[x])
        
        if st.button("Показати графік"):
            data = []
            # If no worker selected, fetch all? Let's default to all if empty.
            if not sel_workers:
                worker_ids_to_fetch = None
            else:
                worker_ids_to_fetch = sel_workers # Logic needs to handle list in query or loop
            
            # Simple loop if list is selected (Supabase 'in' filter is .in_("col", list))
            # But let's build query dynamically inside fetch function if we want optimization.
            # checks:
            report_data = fetch_schedule_report(start_d, end_d, worker_id=None) # Fetch all then filter in DF for flexibility
            
            if report_data:
                df = pd.DataFrame(report_data)
                
                # Filter by Worker locally
                if sel_workers:
                    df = df[df['assigned_worker_id'].isin(sel_workers)]
                
                if not df.empty:
                    # Transform for Display
                    # Columns: Date | Worker | Article | Operation | Qty | Norm | Executed | Unfinished
                    
                    rows = []
                    for _, row in df.iterrows():
                        op_cat = row.get('operations_catalog') or {}
                        prof = row.get('profiles') or {}
                        
                        qty = row.get('quantity', 0)
                        done = row.get('completed_quantity', 0)
                        
                        rows.append({
                            "Дата": pd.to_datetime(row.get('scheduled_start_at')).strftime('%d.%m.%Y'),
                            "Працівник": prof.get('full_name', '-'),
                            "Артикул": op_cat.get('article', '-'),
                            "Операція": row.get('operation_name'),
                            "Кількість": qty,
                            "Час (норм)": row.get('norm_time_per_unit', 0),
                            "Виконано": done,
                            "Невиконано": qty - done,
                            # Hidden useful cols
                            "section": row.get('sections', {}).get('name', '-')
                        })
                    
                    df_view = pd.DataFrame(rows)
                    st.dataframe(df_view, use_container_width=True)
                else:
                    st.info("Даних не знайдено.")
            else:
                st.info("Даних не знайдено.")

    # --- TAB 2: SECTION DAILY REPORT ---
    with tab_section:
        # Section Selector
        sections = db.client.table("sections").select("id, name").execute().data
        s_map = {s['id']: s['name'] for s in sections}
        
        sel_section = st.selectbox("Оберіть дільницю", options=list(s_map.keys()), format_func=lambda x: s_map[x])
        
        if st.button("Згенерувати звіт дільниці"):
            raw_data = fetch_schedule_report(start_d, end_d, section_id=sel_section)
            
            if raw_data:
                df_raw = pd.DataFrame(raw_data)
                
                # Transform
                report_rows = []
                for _, row in df_raw.iterrows():
                    prof = row.get('profiles') or {}
                    orders = row.get('orders') or {}
                    op_cat = row.get('operations_catalog') or {}
                    
                    report_rows.append({
                        "Дата": pd.to_datetime(row.get('scheduled_start_at')).strftime('%Y-%m-%d'),
                        "Замовлення": orders.get('order_number'),
                        "Виріб": orders.get('product_name'),
                        "Операція": row.get('operation_name'),
                        "Працівник": prof.get('full_name'),
                        "План (шт)": row.get('quantity'),
                        "Факт (шт)": row.get('completed_quantity', 0),
                        "Норма часу": row.get('norm_time_per_unit')
                    })
                
                df_rep = pd.DataFrame(report_rows)
                
                st.write(f"### Звіт по дільниці: {s_map[sel_section]}")
                st.dataframe(df_rep, use_container_width=True)
                
                # Download CSV
                csv = df_rep.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Завантажити звіт (CSV)",
                    data=csv,
                    file_name=f"section_report_{s_map[sel_section]}_{start_d}.csv",
                    mime="text/csv",
                    type="primary"
                )
            else:
                st.warning("Немає даних для звіту.")

if __name__ == "__main__":
    main()
