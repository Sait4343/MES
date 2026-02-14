import streamlit as st
from supabase import create_client, Client
from core.config import AppConfig

# Singleton pattern for DB connection
@st.cache_resource
def get_db_client() -> Client:
    try:
        return create_client(AppConfig.SUPABASE_URL, AppConfig.SUPABASE_KEY)
    except Exception as e:
        st.error(f"Failed to connect to Supabase: {e}")
        return None

class DatabaseService:
    def __init__(self):
        self.client = get_db_client()

    def get_user_profile(self, user_id: str):
        """Fetch user profile including role."""
        try:
            response = self.client.table("profiles").select("*").eq("id", user_id).single().execute()
            return response.data
        except Exception as e:
            # Handle case where profile doesn't exist yet
            return None

    def execute_query(self, table: str, query_func):
        """Generic wrapper for DB queries with error handling."""
        try:
            return query_func(self.client.table(table))
        except Exception as e:
            st.error(f"Database Error: {e}")
            return None
