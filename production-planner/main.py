import sys
import os

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
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
        
        # Dashboard Summary (Placeholder)
        col1, col2, col3 = st.columns(3)
        col1.metric("Active Orders", "12") # Todo: Fetch real data
        col2.metric("Delayed Steps", "3")
        col3.metric("Completed Today", "5")

if __name__ == "__main__":
    main()
