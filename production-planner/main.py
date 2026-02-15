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
    layout="wide"
)

# Initialize Supabase
init_supabase()

def main():
    st.title("🏭 MES Production Planner")
    
    user = check_auth()
    
    if not user:
        login()
    else:
        st.sidebar.success(f"Logged in as {user.email}")
        if st.sidebar.button("Logout"):
            logout()
            
        st.markdown(f"""
        ### Welcome, {user.user_metadata.get('full_name', user.email)}!
        
        Use the sidebar to navigate to:
        - **Orders**: View and edit production orders.
        - **Order Details**: Deep dive into specific orders and their history.
        - **Calendar**: Visual production schedule.
        """)
        
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
            st.subheader("Placeholder for other metrics")
            st.caption("Here we can add weekly production rate or worker load.")

if __name__ == "__main__":
    main()
