from core.database import DatabaseService
import streamlit as st
import pandas as pd

class QualityService:
    def __init__(self):
        self.db = DatabaseService()
        self.TABLE = "quality_logs"

    def log_defect(self, order_op_id, defect_type, quantity, reason, user_id=None):
        """Log a new defect record."""
        data = {
            "order_operation_id": order_op_id,
            "defect_type": defect_type,
            "quantity": quantity,
            "reason": reason,
            "logged_by": user_id
        }
        try:
            return self.db.client.table(self.TABLE).insert(data).execute()
        except Exception as e:
            st.error(f"Error logging defect: {e}")
            return None

    def get_defects_stats(self):
        """Get summary of defects by Type and Reason for charts."""
        try:
            # Fetch all logs with related Operation info to know Section info if needed
            # For now, just raw stats
            res = self.db.client.table(self.TABLE).select("defect_type, quantity, reason").execute()
            return pd.DataFrame(res.data)
        except Exception as e:
            return pd.DataFrame()

    def get_recent_logs(self, limit=50):
        """Get recent quality logs."""
        try:
            return self.db.client.table(self.TABLE).select("*").order("logged_at", desc=True).limit(limit).execute().data
        except Exception:
            return []
