import streamlit as st
import pandas as pd
import plotly.express as px
from modules.orders.services import OrderService # To get sections
from modules.maintenance.services import MaintenanceService
from datetime import datetime

st.set_page_config(page_title="Maintenance", page_icon="🛠️", layout="wide")

st.title("🛠️ Технічне Обслуговування (Maintenance)")

# Services
# We reuse OrderService to get sections list easily
order_service = OrderService() 
main_service = MaintenanceService()

# --- SIDEBAR: Report Downtime ---
with st.sidebar:
    st.header("🚨 Повідомити про Поломку")
    sections = order_service.get_sections()
    sec_options = {s['id']: s['name'] for s in sections}
    
    selected_sec_id = st.selectbox("Дільниця / Обладнання", options=list(sec_options.keys()), format_func=lambda x: sec_options[x])
    reason = st.text_input("Причина зупинки", placeholder="Зламався інструмент, немає світла...")
    
    if st.button("REPORT DOWNTIME", type="primary"):
        if reason:
            main_service.report_downtime(selected_sec_id, reason)
            st.success("Зупинку зареєстровано!")
            st.rerun()
        else:
            st.error("Вкажіть причину!")

# --- MAIN CONTENT ---

# 1. Active Downtimes
st.markdown("### 🛑 Активні Простої (Active Downtime)")
active_downtimes = main_service.get_active_downtime()

if active_downtimes:
    for dt in active_downtimes:
        sec_name = dt.get('sections', {}).get('name', 'Unknown')
        with st.container(border=True):
            cols = st.columns([1, 2, 2, 1])
            cols[0].markdown(f"**{sec_name}**")
            cols[1].warning(f"Причина: {dt['reason']}")
            cols[2].info(f"Початок: {dt['start_time']}")
            
            if cols[3].button("✅ Вирішено", key=f"resolve_{dt['id']}"):
                main_service.resolve_downtime(dt['id'])
                st.rerun()
else:
    st.success("Всі дільниці працюють у штатному режимі! (No active downtime)")

st.divider()

# 2. History
st.markdown("### 📜 Журнал Простоїв")
history = main_service.get_downtime_history()
if history:
    df_hist = pd.DataFrame(history)
    
    # Flatten section name
    if 'sections' in df_hist.columns:
        df_hist['section_name'] = df_hist['sections'].apply(lambda x: x.get('name') if isinstance(x, dict) else '')
    
    st.dataframe(
        df_hist[['section_name', 'reason', 'start_time', 'end_time', 'status']], 
        use_container_width=True
    )
else:
    st.info("Журнал порожній.")
