
import streamlit as st
from core.database import get_database
import uuid

# Mock secrets if not present (for local run without full env)
if not st.secrets:
    print("Warning: st.secrets not found. Ensure SUPABASE_URL and SUPABASE_KEY are set.")
    # We might need to stop here if we can't access secrets, but let's assume the environment is set up for the user's workspace
    
try:
    db = get_database()
    print("Database connection initialized.")
    
    # Try to select from the new table
    # We use a random UUID that definitely won't match anything, just to test the table existence query
    dummy_id = str(uuid.uuid4())
    
    print(f"Attempting to query strategy_reports for dummy project_id: {dummy_id}")
    reports = db.get_strategy_reports(dummy_id)
    
    print("Query successful!")
    print(f"Result (should be empty list): {reports}")
    
    if isinstance(reports, list):
        print("✅ VERIFICATION SUCCESS: 'strategy_reports' table exists and is accessible.")
    else:
        print("❌ VERIFICATION FAILED: Unexpected return type.")

except Exception as e:
    print(f"❌ VERIFICATION FAILED: {e}")
    print("This likely means the 'strategy_reports' table does not exist or permissions are incorrect.")
