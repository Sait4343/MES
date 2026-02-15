import sys
import os

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
import pandas as pd
import plotly.express as px
from modules.orders.services import OrderService
from auth import login, logout, check_auth
from utils import init_supabase

st.set_page_config(
    page_title="MES Production Planner",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize Supabase
init_supabase()

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
        
        # Role Simulation
        st.markdown("### 🎭 Role Switcher (Sim)")
        current_role = st.selectbox(
            "Current Perspective", 
            ["Admin", "Planner", "Worker"],
            index=0
        )
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
    st.title("🏭 MES Production Planner")
    
    user = check_auth()
    
    if not user:
        login()
    else:
        st.sidebar.divider()
        st.sidebar.caption(f"Logged in as {user.email}")
        if st.sidebar.button("Logout"):
            logout()
            
        st.markdown(f"### Welcome, {user.user_metadata.get('full_name', user.email)}!")
        st.info(f"You are viewing as: **{current_role}**")
        
        # Dashboard Summary
        service = OrderService()
        orders = service.get_orders()
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Active Orders", len(orders))
        
        # Calculate other metrics if possible or keep placeholder
        col2.metric("Delayed Steps", "3") # Todo
        col3.metric("Completed Today", "5") # Todo
        
        st.divider()
        
        # --- Charts ---
        c_chart1, c_chart2 = st.columns(2)
        
        with c_chart1:
            st.subheader("📍 Розподіл замовлень по дільницях")
            dist = service.get_active_orders_distribution()
            
            if dist:
                df_dist = pd.DataFrame(list(dist.items()), columns=['Section', 'Count'])
                fig = px.pie(df_dist, values='Count', names='Section', title='Orders by Current Section')
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Немає активних замовлень для відображення.")
        
        with c_chart2:
            st.subheader("📊 Production Metrics")
            st.caption("Weekly throughput and efficiency metrics will appear here.")

if __name__ == "__main__":
    main()
