import sys
import os

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from modules.orders.services import OrderService
from auth import login, logout, check_auth
from utils import init_supabase
from ui.components import load_custom_css, render_kpi_card

st.set_page_config(
    page_title="MES Production Planner",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize Supabase
init_supabase()
load_custom_css()

def main():
    # --- 1. Custom Navigation & Role Simulation ---
    # Hide default sidebar nav
    st.markdown("""
    <style>
    [data-testid="stSidebarNav"] {display: none;}
    </style>
    """, unsafe_allow_html=True)

    with st.sidebar:
        st.title("🏭 MES System")
        
        # Role Simulation (Buttons)
        st.markdown("### 🎭 Change Role")
        r1, r2, r3 = st.columns(3)
        
        if r1.button("👮"):
            st.session_state["sim_role"] = "Admin"
            st.rerun()
        if r2.button("📅"):
            st.session_state["sim_role"] = "Planner"
            st.rerun()
        if r3.button("👷"):
            st.session_state["sim_role"] = "Worker"
            st.rerun()
            
        current_role = st.session_state.get("sim_role", "Admin")
        st.caption(f"View: {current_role}")
        st.divider()
        
        # Navigation Logic
        st.markdown("### 🧭 Navigation")
        
        if current_role == "Admin":
            st.page_link("main.py", label="Dashboard", icon="🏠")
            st.page_link("pages/01_Orders.py", label="Orders List", icon="📋")
            st.page_link("pages/02_Order_Details.py", label="Detailed Planning", icon="📅")
            st.page_link("pages/03_Worker_Schedule.py", label="Worker Schedule", icon="👷")
            st.page_link("pages/04_Quality_Control.py", label="Quality Control", icon="🔍")
            st.page_link("pages/05_Maintenance.py", label="Maintenance", icon="🛠️")
            st.page_link("pages/06_My_Tasks.py", label="Worker Interface", icon="🔨")
            # st.page_link("pages/04_Admin.py", label="System Admin", icon="⚙️")

        elif current_role == "Planner":
            st.page_link("main.py", label="Dashboard", icon="🏠")
            st.page_link("pages/01_Orders.py", label="Orders List", icon="📋")
            st.page_link("pages/02_Order_Details.py", label="Detailed Planning", icon="📅")
            st.page_link("pages/04_Quality_Control.py", label="Quality Control", icon="🔍")
            st.page_link("pages/05_Maintenance.py", label="Maintenance", icon="🛠️")
        
        elif current_role == "Worker":
            st.page_link("pages/06_My_Tasks.py", label="My Tasks", icon="🔨")
            st.info("Worker view is restricted to assigned tasks only.")

    # --- 2. Main Content ---
    st.title("🏭 MES Enterprise Control Tower")
    st.caption("Real-time Production Monitoring")
    
    user = check_auth()
    
    if not user:
        login()
    else:
        st.sidebar.divider()
        st.sidebar.caption(f"Logged in as {user.email}")
        if st.sidebar.button("Logout"):
            logout()
            
        st.markdown(f"### 👋 Welcome back, {user.user_metadata.get('full_name', user.email)}")
        
        # Dashboard Content
        service = OrderService()
        orders = service.get_orders() # Using all orders as proxy for active
        
        st.markdown("#### 📊 Key Performance Indicators (KPIs)")
        
        # Custom KPI Cards
        k1, k2, k3, k4 = st.columns(4)
        with k1: render_kpi_card("Active Orders", str(len(orders)), delta="+2", color="green")
        with k2: render_kpi_card("Shift OEE", "87%", delta="+1.2%", color="green")
        with k3: render_kpi_card("Downtime", "12m", delta="-5m", color="green") # Green because down implies improvement if neg
        with k4: render_kpi_card("Pending Tasks", "24", delta="+4", color="red") # More pending might be bad

        st.divider()
        
        # --- Charts ---
        c_chart1, c_chart2 = st.columns([1, 1])
        
        with c_chart1:
            st.subheader("📍 Shop Floor Activity")
            dist = service.get_active_orders_distribution()
            
            if dist:
                df_dist = pd.DataFrame(list(dist.items()), columns=['Section', 'Count'])
                # Use a Donut chart for modern look
                fig = px.pie(df_dist, values='Count', names='Section', hole=0.4)
                fig.update_layout(showlegend=True, margin=dict(t=0, b=0, l=0, r=0))
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No active production data.")
        
        with c_chart2:
            st.subheader("⚠️ Critical Alerts")
            # Simulated Alerts for "Management Level" view
            alerts = [
                {"msg": "Section A: Conveyor speed variation detected", "time": "10:45 AM", "severity": "warning"},
                {"msg": "Quality: Defect rate spike in Batch #202", "time": "09:30 AM", "severity": "critical"},
                {"msg": "Maintenance: Scheduled check for Robot Arm 2", "time": "Tomorrow", "severity": "info"},
            ]
            
            for alert in alerts:
                emoji = "🔴" if alert['severity'] == "critical" else "🟡" if alert['severity'] == "warning" else "ℹ️"
                st.info(f"{emoji} **{alert['time']}** | {alert['msg']}")

if __name__ == "__main__":
    main()
