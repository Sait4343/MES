import streamlit as st
import pandas as pd
from utils import fetch_orders, fetch_order_details
from auth import require_auth

st.set_page_config(page_title="Order Details", layout="wide")
require_auth()

st.title("🔍 Order Details")

# Order Selection
orders_df = fetch_orders()
if orders_df.empty:
    st.info("No orders found.")
    st.stop()

order_number = st.selectbox("Select Order", orders_df['order_number'].unique())

if order_number:
    order_id = orders_df[orders_df['order_number'] == order_number]['id'].iloc[0]
    details = fetch_order_details(order_id)
    
    if details:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("General Info")
            st.write(f"**Product:** {details['product_name']}")
            st.write(f"**Article:** {details.get('article', '-')}")
            st.write(f"**Quantity:** {details['quantity']}")
            st.write(f"**Customer:** {details.get('contractor', '-')}")
            
        with col2:
            st.subheader("Dates")
            st.write(f"**Start Date:** {details.get('start_date', '-')}")
            st.write(f"**Shipping Date:** {details.get('shipping_date', '-')}")
            st.write(f"**Status:** {details.get('status', 'Active')}") # Todo: Calculate overall status
            
        st.subheader("Production Timeline")
        steps = details.get('production_steps', [])
        
        # Sort steps by a predefined order if possible, or just display as is
        # For now, just display list
        if steps:
            steps_df = pd.DataFrame(steps)
            steps_df = steps_df[['step_name', 'status', 'started_at', 'completed_at', 'assigned_worker_id']]
            st.dataframe(steps_df, use_container_width=True)
        else:
            st.info("No production steps found.")
