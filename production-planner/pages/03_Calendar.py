import streamlit as st
import pandas as pd
import plotly.express as px
from utils import fetch_orders
from auth import require_auth

st.set_page_config(page_title="Production Calendar", layout="wide")
require_auth()

st.title("📅 Production Schedule")

df = fetch_orders()

if df.empty:
    st.info("No orders found.")
    st.stop()

# Prepare data for Gantt chart
# Ensure date columns are datetime
df['start_date'] = pd.to_datetime(df['start_date'])
df['shipping_date'] = pd.to_datetime(df['shipping_date'])

# Filter incomplete records
gantt_df = df.dropna(subset=['start_date', 'shipping_date'])

if gantt_df.empty:
    st.warning("No orders with valid start and shipping dates.")
else:
    # Color by status if possible, or just by order
    # For now, let's just use Product Name as color
    fig = px.timeline(
        gantt_df, 
        x_start="start_date", 
        x_end="shipping_date", 
        y="order_number", 
        color="product_name",
        hover_data=["quantity", "contractor", "comment"],
        title="Order Timeline"
    )
    
    fig.update_yaxes(autorange="reversed") # Show newest on top? Or just standard
    st.plotly_chart(fig, use_container_width=True)

# Upcoming Deliveries Table
st.subheader("Upcoming Shipping Dates")
upcoming = df[['order_number', 'product_name', 'shipping_date', 'quantity', 'contractor']].sort_values('shipping_date')
st.dataframe(upcoming.head(10), use_container_width=True)
