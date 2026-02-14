import streamlit as st
from supabase import create_client, Client
import pandas as pd
from datetime import datetime
import time

@st.cache_resource
def init_supabase() -> Client:
    """Initialize Supabase client."""
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except FileNotFoundError:
        st.error("Secrets file not found. Please create .streamlit/secrets.toml")
        st.stop()
    except KeyError:
        st.error("Supabase credentials not found in secrets.toml")
        st.stop()

supabase = init_supabase()

def fetch_orders():
    """Fetch all orders with their production steps."""
    try:
        response = supabase.table("orders").select("*, production_steps(*)").execute()
        
        if not response.data:
            return pd.DataFrame()
            
        data = response.data
        
        # Flatten the data for display
        flattened_data = []
        for order in data:
            order_row = order.copy()
            steps = order_row.pop("production_steps", [])
            
            # Add step statuses as columns
            for step in steps:
                order_row[f"step_{step['step_name']}"] = step['status']
                
            flattened_data.append(order_row)
            
        return pd.DataFrame(flattened_data)
    except Exception as e:
        st.error(f"Error fetching orders: {e}")
        return pd.DataFrame()

def fetch_order_details(order_id: str):
    """Fetch details for a single order."""
    try:
        response = supabase.table("orders").select("*, production_steps(*)").eq("id", order_id).single().execute()
        return response.data
    except Exception as e:
        st.error(f"Error fetching order details: {e}")
        return None

def update_order(order_id: str, updates: dict):
    """Update order fields."""
    try:
        data = supabase.table("orders").update(updates).eq("id", order_id).execute()
        return data
    except Exception as e:
        st.error(f"Error updating order: {e}")
        return None

def update_step_status(order_id: str, step_name: str, status: str, worker_id: str = None):
    """Update the status of a production step."""
    try:
        # Get step ID
        step_response = supabase.table("production_steps")\
            .select("id")\
            .eq("order_id", order_id)\
            .eq("step_name", step_name)\
            .single()\
            .execute()
            
        if not step_response.data:
            st.error(f"Step {step_name} not found for order {order_id}")
            return None
            
        step_id = step_response.data['id']
        
        updates = {
            "status": status,
            "updated_at": datetime.now().isoformat()
        }
        
        if status == "in_progress":
            updates["started_at"] = datetime.now().isoformat()
            if worker_id:
                updates["assigned_worker_id"] = worker_id
        elif status == "done":
            updates["completed_at"] = datetime.now().isoformat()
            
        data = supabase.table("production_steps").update(updates).eq("id", step_id).execute()
        return data
    except Exception as e:
        st.error(f"Error updating step status: {e}")
        return None

def create_order(order_data: dict):
    """Create a new order."""
    try:
        data = supabase.table("orders").insert(order_data).execute()
        return data
    except Exception as e:
        st.error(f"Error creating order: {e}")
        return None
