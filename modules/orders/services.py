from core.database import DatabaseService
import streamlit as st

class OrderService:
    def __init__(self):
        self.db = DatabaseService()

    def get_orders(self):
        """Fetch all orders ordered by creation date."""
        try:
            return self.db.client.table("orders").select("*").order("created_at", desc=True).execute().data
        except Exception as e:
            st.error(f"Error fetching orders: {e}")
            return []

    def create_order(self, order_data):
        """Create a new order."""
        try:
            return self.db.client.table("orders").insert(order_data).execute()
        except Exception as e:
            st.error(f"Error creating order: {e}")
            return None

    def update_order(self, order_id, updates):
        """Update an existing order."""
        try:
            return self.db.client.table("orders").update(updates).eq("id", order_id).execute()
        except Exception as e:
            st.error(f"Error updating order: {e}")
            return None

    def delete_order(self, order_id):
        """Delete an order (Admin only)."""
        try:
            return self.db.client.table("orders").delete().eq("id", order_id).execute()
        except Exception as e:
            st.error(f"Error deleting order: {e}")
            return None
