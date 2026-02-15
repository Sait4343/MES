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
        """Fetch all operations for a specific order with related data."""
        try:
            # Fetch operations without workers join (workaround for missing FK)
            response = self.db.client.table("order_operations").select(
                "*, sections(name), operations_catalog(operation_key, article)"
            ).eq("order_id", order_id).order("sort_order").execute()
            
            ops_data = response.data
            
            if not ops_data:
                return []
            
            # Fetch workers separately
            workers_res = self.db.client.table("workers").select("id, full_name").execute()
            workers_map = {w['id']: w for w in workers_res.data} if workers_res.data else {}
            
            # Manually add worker info to each operation
            for op in ops_data:
                worker_id = op.get('assigned_worker_id')
                if worker_id and worker_id in workers_map:
                    op['workers'] = workers_map[worker_id]
                else:
                    op['workers'] = None
            
            return ops_data
            
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
        """Fetch all workers from 'workers' table."""
        try:
            return self.db.client.table("workers").select("id, full_name, operation_types, section_id").execute().data
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
        """
        Find workers compatible with a section.
        Priority 1: Worker has section_id matching this section.
        Priority 2: Worker has this section name in 'operation_types'.
        """
        try:
            # 1. Get Section ID
            sec_res = self.db.client.table("sections").select("id").eq("name", section_name).execute()
            if not sec_res.data:
                return []
            sec_id = sec_res.data[0]['id']

            # 2. Fetch all workers (optimizable with complex OR query, but fetching all is safer for small teams)
            # OR logic: section_id.eq.X OR operation_types.cs.{Name}
            # PostgREST syntax for OR: or=(section_id.eq.X,operation_types.cs.{Name})
            
            or_filter = f"section_id.eq.{sec_id},operation_types.cs.{{{section_name}}}"
            return self.db.client.table("workers").select("id, full_name, section_id").or_(or_filter).execute().data
            
        except Exception as e:
            # Fallback to simple query if complex filter fails
            # st.error(f"Error fetching section workers: {e}")
            return []

    def delete_order_operation(self, op_id):
        try:
            self.db.client.table("order_operations").delete().eq("id", op_id).execute()
            return True
        except Exception as e:
            st.error(f"Error deleting op: {e}")
            return False

    def get_worker_tasks(self, worker_id):
        """Fetch all tasks assigned to a specific worker."""
        try:
            # Join with orders to get context (Order #, Article)
            # Join with operations_catalog to get operation name/key
            return self.db.client.table("order_operations").select(
                "*, orders(order_number, article, customer_name), operations_catalog(operation_key, section)"
            ).eq("assigned_worker_id", worker_id).order("scheduled_start_at").execute().data
        except Exception as e:
            # st.error(f"Error fetching tasks: {e}")
            return []

    def update_operation_status(self, op_id, new_status, quantity_done=0):
        """Update status and progress of an operation."""
        data = {"status": new_status}
        if quantity_done > 0:
            data["completed_quantity"] = quantity_done
        
        # If finishing, set actual end time? (Optional, let's keep it simple)
        if new_status == 'done':
            # data['actual_end_at'] = datetime.now().isoformat()
            pass
            
        try:
            return self.db.client.table("order_operations").update(data).eq("id", op_id).execute()
        except Exception as e:
            return None

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
                        # Now uses the combined strict + loose lookup from 'workers' table
                        qualified = self.get_workers_for_section(section_name)
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
    def get_all_orders_with_operations(self):
        """
        Fetch all orders with their operations, sections, and status.
        Optimized for visualization.
        """
        try:
            # Fetch all orders
            orders = self.db.client.table("orders").select("id, order_number, product_name, start_date, end_date").execute().data
            
            # Fetch all operations (could be heavy, but manageable for MVP)
            # We need: order_id, status, scheduled_start_at, scheduled_end_at, quantity, sections(name), operations_catalog(operation_key)
            ops = self.db.client.table("order_operations").select(
                "order_id, status, scheduled_start_at, scheduled_end_at, quantity, sections(name), operations_catalog(operation_key)"
            ).order("sort_order").execute().data
            
            # Group ops by order
            orders_map = {o['id']: {**o, 'operations': []} for o in orders}
            
            for op in ops:
                oid = op.get('order_id')
                if oid in orders_map:
                    orders_map[oid]['operations'].append(op)
            
            return list(orders_map.values())
        except Exception as e:
            # st.error(f"Error fetching visualization data: {e}")
            return []
