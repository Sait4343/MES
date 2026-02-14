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
            
    # --- Advanced Planning Methods ---
    
    def get_order_operations(self, order_id):
        """Fetch planned operations for an order."""
        try:
            # Join with catalog and sections for names?
            # Supabase join syntax: select(*, other_table(*))
            return self.db.client.table("order_operations").select(
                "*, operations_catalog(article, operation_key), sections(name), profiles(full_name)"
            ).eq("order_id", order_id).order("sort_order").execute().data
        except Exception as e:
            # st.error(f"Error fetching plan: {e}")
            return []

    def get_available_operations(self, section_id=None):
        """Fetch operations from catalog, optionally filtered by section."""
        query = self.db.client.table("operations_catalog").select("*")
        if section_id:
            # We need to map section_id to section name? 
            # Or operations_catalog stores 'section' string.
            # Sections table stores 'name'.
            # We assume user selects Section Object, we get Name.
            pass 
        return query.execute().data

    def get_workers_for_section(self, section_name):
        """Find workers who have this section in their 'operation_types'."""
        try:
            # 'operation_types' is text[] or jsonb? user requested text[] in migration.
            # PostgREST filter for array contains: cs (contains)
            return self.db.client.table("profiles").select("*").cs("operation_types", f"{{{section_name}}}").execute().data
        except Exception as e:
            return []

    def create_order_operation(self, data):
        try:
            return self.db.client.table("order_operations").insert(data).execute()
        except Exception as e:
            return None, str(e)
            
    def delete_order_operation(self, op_id):
        try:
            self.db.client.table("order_operations").delete().eq("id", op_id).execute()
            return True
        except Exception as e:
            st.error(f"Error deleting op: {e}")
            return False
