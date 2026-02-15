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

    def fetch_section_workers(self, section_name):
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

    def get_busy_workers(self, start_time, end_time):
        """
        Find workers who are already assigned to operations that overlap with the given time range.
        Overlap: (StartA < EndB) and (EndA > StartB)
        """
        try:
            # We need to query order_operations where dates overlap
            # Supabase/PostgREST doesn't have a simple "overlap" filter for ranges, 
            # so we check: scheduled_start_at < end_time AND scheduled_end_at > start_time
            
            # Note: client.table().select() with filters
            # We can use .lt('scheduled_start_at', end_time).gt('scheduled_end_at', start_time)
            
            response = self.db.client.table("order_operations").select("assigned_worker_id") \
                .lt("scheduled_start_at", end_time.isoformat()) \
                .gt("scheduled_end_at", start_time.isoformat()) \
                .neq("assigned_worker_id", None) \
                .execute()
            
            busy_ids = {row['assigned_worker_id'] for row in response.data}
            return busy_ids
        except Exception as e:
            # print(f"Error checking busy workers: {e}")
            return set()

    def auto_schedule_order(self, order_id, assign_workers=True):
        """
        Automatically calculate start/end dates for all operations in an order.
        Optionally assign free workers.
        Logic: Sequential execution based on sort_order.
        """
        import datetime
        import random
        
        try:
            # 1. Get Order Details for Start Date
            order = self.get_order_by_id(order_id)
            if not order: return False
            
            start_base = order.get('start_date')
            if start_base:
                current_time = datetime.datetime.fromisoformat(start_base)
            else:
                current_time = datetime.datetime.now()

            # 2. Get All Operations Sorted
            ops = self.db.client.table("order_operations").select("*, sections(name)").eq("order_id", order_id).order("sort_order").execute().data
            
            # Cache workers to avoid repeated DB calls if possible, but availability changes per slot
            # So we fetch qualified workers once per section if needed, but we need strictly per-slot availability
            
            for op in ops:
                # Calculate Duration (Minutes)
                qty = op.get('quantity', 0)
                norm = op.get('norm_time_per_unit', 0) or 0
                duration_mins = qty * norm
                
                # If 0 duration, assume default small window or 0
                if duration_mins <= 0: duration_mins = 60 

                end_time = current_time + datetime.timedelta(minutes=duration_mins)
                
                update_data = {
                    "scheduled_start_at": current_time.isoformat(),
                    "scheduled_end_at": end_time.isoformat()
                }

                # --- WORKER ASSIGNMENT ---
                if assign_workers:
                    section_name = op.get('sections', {}).get('name')
                    if section_name:
                        # 1. Get Qualified Workers for this section
                        qualified = self.fetch_section_workers(section_name)
                        qualified_ids = [w['id'] for w in qualified]
                        
                        if qualified_ids:
                            # 2. Check who is busy in this specific slot
                            busy_ids = self.get_busy_workers(current_time, end_time)
                            
                            # 3. Filter
                            available = [uid for uid in qualified_ids if uid not in busy_ids]
                            
                            if available:
                                # Assign first available (or random)
                                # Logic: "not attached to any of the sections" - interpreted as just "free"
                                update_data["assigned_worker_id"] = available[0] 
                            else:
                                # No one available? Keep current or set None? 
                                # Let's keep existing if valid, or leave as is.
                                # Requirement says "attach according to those who are free"
                                pass

                # Update Record
                self.db.client.table("order_operations").update(update_data).eq("id", op['id']).execute()
                
                # Next starts when this ends (Sequential)
                current_time = end_time
                
            return True
        except Exception as e:
            st.error(f"Auto-schedule failed: {e}")
            return False
    def get_active_orders_distribution(self):
        """
        Calculate distribution of active orders by their current section.
        'Current section' is defined as the section of the first incomplete operation.
        """
        try:
            # 1. Fetch all active orders (heuristic: not completed/shipped, or just all for now)
            # For accurate status, we might need an 'orders' status column, but let's iterate all.
            orders = self.get_orders()
            distribution = {}

            for order in orders:
                # 2. Get operations for this order
                # This could be N+1 slow, but optimized later with a view or join.
                ops = self.db.client.table("order_operations").select("status, sections(name)") \
                    .eq("order_id", order['id']) \
                    .order("sort_order") \
                    .execute().data
                
                current_section = "Не сплановано"
                
                # Find first non-done operation
                for op in ops:
                    if op.get('status') != 'done':
                        sec = op.get('sections')
                        current_section = sec.get('name') if sec else "Без дільниці"
                        break
                else:
                     # If loops finishes (all done), check if ops existed
                     if ops: current_section = "Готово / Склад"
                
                distribution[current_section] = distribution.get(current_section, 0) + 1
                
            return distribution
        except Exception as e:
            # st.error(f"Error calculating distribution: {e}")
            return {}
