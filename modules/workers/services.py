from core.database import DatabaseService
import streamlit as st

class WorkerService:
    def __init__(self):
        self.db = DatabaseService()

    def get_all_workers(self):
        """Fetch all user profiles."""
        try:
            return self.db.client.table("profiles").select("*").order("full_name").execute().data
        except Exception as e:
            st.error(f"Error fetching workers: {e}")
            return []

    def update_worker_role(self, user_id, new_role):
        """Update a user's role (Admin only)."""
        try:
            return self.db.client.table("profiles").update({"role": new_role}).eq("id", user_id).execute()
        except Exception as e:
            st.error(f"Error updating role: {e}")
            return None
