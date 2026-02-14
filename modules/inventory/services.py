from core.database import DatabaseService
import streamlit as st

class InventoryService:
    def __init__(self):
        self.db = DatabaseService()

    def get_items(self):
        """Fetch all inventory items."""
        try:
            return self.db.client.table("inventory").select("*").order("item_name").execute().data
        except Exception as e:
            st.error(f"Error fetching inventory: {e}")
            return []

    def add_item(self, data):
        """Add a new inventory item."""
        try:
            return self.db.client.table("inventory").insert(data).execute()
        except Exception as e:
            st.error(f"Error adding item: {e}")
            return None

    def update_item(self, item_id, data):
        """Update an inventory item."""
        try:
            return self.db.client.table("inventory").update(data).eq("id", item_id).execute()
        except Exception as e:
            st.error(f"Error updating item: {e}")
            return None

    def delete_item(self, item_id):
        """Delete an inventory item."""
        try:
            return self.db.client.table("inventory").delete().eq("id", item_id).execute()
        except Exception as e:
            st.error(f"Error deleting item: {e}")
            return None
