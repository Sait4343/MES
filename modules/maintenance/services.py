from core.database import DatabaseService
import streamlit as st
from datetime import datetime
import pandas as pd

class MaintenanceService:
    def __init__(self):
        self.db = DatabaseService()
        self.TABLE = "equipment_downtime"

    def report_downtime(self, section_id, reason, user_id=None):
        """Report a breakdown (Open a downtime event)."""
        data = {
            "section_id": section_id,
            "reason": reason,
            "start_time": datetime.now().isoformat(),
            "status": "open",
            "logged_by": user_id
        }
        try:
            return self.db.client.table(self.TABLE).insert(data).execute()
        except Exception as e:
            st.error(f"Error reporting downtime: {e}")
            return None

    def resolve_downtime(self, downtime_id):
        """Close a downtime event."""
        data = {
            "end_time": datetime.now().isoformat(),
            "status": "resolved"
        }
        try:
            return self.db.client.table(self.TABLE).update(data).eq("id", downtime_id).execute()
        except Exception as e:
            st.error(f"Error resolving downtime: {e}")
            return None

    def get_active_downtime(self, section_id=None):
        """Get currently open downtime events."""
        try:
            query = self.db.client.table(self.TABLE).select("*, sections(name)").eq("status", "open")
            if section_id:
                query = query.eq("section_id", section_id)
            return query.execute().data
        except Exception:
            return []

    def get_downtime_history(self):
        """Get history of downtimes."""
        try:
            return self.db.client.table(self.TABLE).select("*, sections(name)").order("start_time", desc=True).limit(50).execute().data
        except Exception:
            return []
