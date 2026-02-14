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
    
    def get_order_by_id(self, order_id):
        """Fetch a single order by ID."""
        try:
            data = self.db.client.table("orders").select("*").eq("id", order_id).execute().data
            return data[0] if data else None
        except Exception as e:
            return None

    def get_order_operations(self, order_id):
        """Fetch planned operations for an order with related names."""
        try:
            # We fetch everything and manually join or use Supabase deep joins
            # Note: Supabase-py syntax for foreign key joins: table(column, ...)
            response = self.db.client.table("order_operations").select(
                "*, sections(name), profiles(full_name), operations_catalog(operation_key, article)"
            ).eq("order_id", order_id).order("sort_order").execute()
            return response.data
        except Exception as e:
            st.error(f"Error fetching plan: {e}")
            return []

    def get_sections(self):
        """Fetch all sections."""
        try:
            return self.db.client.table("sections").select("*").order("name").execute().data
        except Exception:
            return []

    def get_all_workers(self):
        """Fetch all workers (for assignment dropdowns)."""
        try:
            return self.db.client.table("profiles").select("id, full_name, operation_types").eq("role", "worker").execute().data
        except Exception:
            return []

    def get_available_operations(self, section_name=None):
        """Fetch operations from catalog."""
        try:
            query = self.db.client.table("operations_catalog").select("*")
            if section_name:
                query = query.eq("section", section_name)
            return query.execute().data
        except Exception:
            return []

    def create_order_operation(self, data):
        try:
            return self.db.client.table("order_operations").insert(data).execute()
        except Exception as e:
            st.error(f"Error adding operation: {e}")
            return None
            
    def update_order_operation(self, op_id, data):
        try:
            return self.db.client.table("order_operations").update(data).eq("id", op_id).execute()
        except Exception as e:
            st.error(f"Error updating operation: {e}")
            return None

    def get_workers_for_section(self, section_name):
        """Find workers who have this section in their 'operation_types'."""
        try:
            # 'operation_types' is text[]
            # PostgREST filter for array contains: cs (contains)
            # Format: {Value} for array literal
            return self.db.client.table("profiles").select("*").cs("operation_types", f"{{{section_name}}}").execute().data
        except Exception as e:
            # st.error(f"Error fetching workers: {e}")
            return []

    def delete_order_operation(self, op_id):
        try:
            self.db.client.table("order_operations").delete().eq("id", op_id).execute()
            return True
        except Exception as e:
            st.error(f"Error deleting op: {e}")
            return False
