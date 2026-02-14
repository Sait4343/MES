import streamlit as st
from core import auth
from core.config import AppConfig
from ui import layout

# Import Modules
from modules.dashboard import view as dashboard_view
from modules.orders import view as orders_view
from modules.planning import view as planning_view
from modules.inventory import view as inventory_view
from modules.workers import view as workers_view
from modules.calendar import view as calendar_view
from modules.analytics import view as analytics_view
from modules.settings import view as settings_view

# Page Config
st.set_page_config(
    page_title=AppConfig.APP_NAME,
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    # 1. Auth Guard
    auth.require_auth()

    # 2. Layout & Navigation
    selected_page = layout.render_sidebar()

    # 3. Routing
    if selected_page == "dashboard":
        dashboard_view.render()
        
    elif selected_page == "orders":
        orders_view.render()
        
    elif selected_page == "planning":
        planning_view.render()
        
    elif selected_page == "inventory":
        inventory_view.render()
        
    elif selected_page == "workers":
        workers_view.render()
        
    elif selected_page == "calendar":
        calendar_view.render()
        
    elif selected_page == "analytics":
        analytics_view.render()

    elif selected_page == "operations":
        from modules.operations import view as ops_view
        ops_view.render()

    elif selected_page == "sections":
        from modules.sections import view as sections_view
        sections_view.render()

    elif selected_page == "settings":
        settings_view.render()

if __name__ == "__main__":
    main()
