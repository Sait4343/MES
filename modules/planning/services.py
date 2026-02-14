from core.database import DatabaseService
import streamlit as st
import pandas as pd
from core.config import StepStatus

class PlanningService:
    def __init__(self):
        self.db = DatabaseService()
        self.step_order = [
            'cutting', 'basting', 'sewing', 'overlock', 
            'completing', 'edging', 'finishing', 'fixing', 'packing'
        ]

    def get_planning_dataframe(self):
        """
        Fetch all orders and their steps, returning a flattened structure for the data editor.
        Returns: pandas DataFrame, Dictionary mapping (order_id, step_name) -> step_id
        """
        try:
            # 1. Fetch Orders
            orders = self.db.client.table("orders").select("*").order("created_at", desc=True).execute().data
            if not orders:
                return pd.DataFrame(), {}

            # 2. Fetch All Steps
            steps = self.db.client.table("production_steps").select("*").execute().data
            
            # Map steps: order_id -> {step_name: {status: ..., id: ...}}
            steps_map = {}
            step_id_map = {} # (order_id, step_name) -> step_id
            
            for s in steps:
                oid = s['order_id']
                sname = s['step_name']
                if oid not in steps_map:
                    steps_map[oid] = {}
                steps_map[oid][sname] = s['status']
                step_id_map[(oid, sname)] = s['id']

            # 3. Build Flattened Rows
            rows = []
            for o in orders:
                row = {
                    "id": o['id'], # Hidden ID for updates
                    "Order #": o['order_number'],
                    "Product": o['product_name'],
                    "Article": o.get('article', ''),
                    "Qty": o['quantity'],
                    "Contractor": o.get('contractor', ''),
                    "Start Date": pd.to_datetime(o['start_date']) if o.get('start_date') else None,
                    "Ship Date": pd.to_datetime(o['shipping_date']) if o.get('shipping_date') else None,
                    "Comment": o.get('comment', '')
                }
                
                # Add Steps
                o_steps = steps_map.get(o['id'], {})
                for step_name in self.step_order:
                    # Default to not_started if missing (shouldn't happen with trigger)
                    row[step_name.title()] = o_steps.get(step_name, StepStatus.NOT_STARTED)
                
                rows.append(row)

            return pd.DataFrame(rows), step_id_map

        except Exception as e:
            st.error(f"Error fetching planning data: {e}")
            return pd.DataFrame(), {}

    def save_changes(self, edited_rows, original_data, step_id_map):
        """
        Process changes from st.data_editor.
        edited_rows: Dict[int, Dict[str, Any]] (Mapping row index to changed col/val)
        original_data: DataFrame used in the editor
        step_id_map: Dict[(order_id, step_name), step_id]
        """
        if not edited_rows:
            return

        for idx_str, changes in edited_rows.items():
            idx = int(idx_str)
            row_data = original_data.iloc[idx]
            order_id = row_data['id']
            
            # Separate updates for Orders table and Production Steps table
            order_updates = {}
            
            for col, new_value in changes.items():
                # Check if it's a Step Column
                lower_col = col.lower()
                if lower_col in self.step_order:
                    # It's a step status update
                    step_name = lower_col
                    step_id = step_id_map.get((order_id, step_name))
                    
                    if step_id:
                        # Update specific step
                        self.update_step_status(step_id, new_value)
                else:
                    # It's an Order field update
                    # Map display names back to DB columns
                    db_col = self._map_col_to_db(col)
                    if db_col:
                         # Handle dates
                        if "date" in db_col and new_value:
                            # Ensure YYYY-MM-DD
                             order_updates[db_col] = str(new_value).split('T')[0]
                        else:
                            order_updates[db_col] = new_value

            # Apply Order Updates
            if order_updates:
                self.db.client.table("orders").update(order_updates).eq("id", order_id).execute()

    def update_step_status(self, step_id, new_status):
        """Helper to update single step."""
        updates = {"status": new_status, "updated_at": "now()"}
        if new_status == StepStatus.DONE:
                updates["completed_at"] = "now()"
        elif new_status == StepStatus.IN_PROGRESS:
                updates["started_at"] = "now()"
        
        self.db.client.table("production_steps").update(updates).eq("id", step_id).execute()

    def _map_col_to_db(self, col_name):
        mapping = {
            "Order #": "order_number",
            "Product": "product_name",
            "Article": "article",
            "Qty": "quantity",
            "Contractor": "contractor",
            "Start Date": "start_date",
            "Ship Date": "shipping_date",
            "Comment": "comment"
        }
        return mapping.get(col_name)
