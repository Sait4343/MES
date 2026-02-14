import streamlit as st
from streamlit_calendar import calendar
from core.database import DatabaseService
import datetime

def render():
    st.header("🗓️ Календар виробництва")
    
    db = DatabaseService()
    
    # Fetch orders with dates
    try:
        response = db.client.table("orders").select("id, order_number, product_name, shipping_date, start_date").execute()
        orders = response.data
    except Exception as e:
        st.error(f"Error fetching orders: {e}")
        orders = []

    if not orders:
        st.info("Немає запланованих подій.")
        return

    # Transform to Calendar Events
    events = []
    for o in orders:
        title = f"{o['order_number']} | {o['product_name']}"
        
        # Shipping Date (Red event)
        if o.get('shipping_date'):
            events.append({
                "title": f"🚢 SHIP: {title}",
                "start": o['shipping_date'],
                "backgroundColor": "#FF6B6B",
                "borderColor": "#FF6B6B",
                "allDay": True
            })
            
        # Start Date (Green event)
        if o.get('start_date'):
             events.append({
                "title": f"🚀 START: {title}",
                "start": o['start_date'],
                "backgroundColor": "#4ECDC4",
                "borderColor": "#4ECDC4",
                "allDay": True
            })

    # Calendar Options
    calendar_options = {
        "headerToolbar": {
            "left": "today prev,next",
            "center": "title",
            "right": "dayGridMonth,timeGridWeek,listMonth"
        },
        "initialView": "dayGridMonth",
        "navLinks": True,
        "selectable": True,
        "editable": False,
    }
    
    # Render
    calendar(
        events=events,
        options=calendar_options,
        custom_css="""
        .fc-event-past {
            opacity: 0.8;
        }
        .fc-event-time {
            font-style: italic;
        }
        .fc-event-title {
            font-weight: 700;
        }
        .fc-toolbar-title {
            font-size: 2rem;
        }
        """
    )
    
    st.caption("🔴 Червоний - Дата відвантаження | 🟢 Зелений - Дата початку")
