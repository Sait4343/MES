import streamlit as st
import sys
import os

# Add production-planner to sys.path to import utils
current_dir = os.path.dirname(os.path.abspath(__file__))
planner_dir = os.path.join(current_dir, "production-planner")
sys.path.append(planner_dir)

try:
    from utils import init_supabase
except ImportError as e:
    st.error(f"Failed to import utils: {e}")
    st.stop()

def check_schema():
    st.title("Database Schema Verification")
    
    try:
        client = init_supabase()
    except Exception as e:
        st.error(f"Failed to initialize Supabase: {e}")
        return

    tables = ["sections", "operations_catalog", "order_operations"]
    missing = []
    
    for table in tables:
        try:
            # Try to select 1 row to check existence
            client.table(table).select("id").limit(1).execute()
            st.success(f"✅ Table **{table}** exists and is accessible.")
        except Exception as e:
            st.error(f"❌ Table **{table}** check failed.")
            with st.expander("Error Details"):
                st.write(e)
            missing.append(table)
            
    if not missing:
        st.success("🎉 All required tables are present!")
        print("SCHEMA_VERIFICATION_PASSED")
    else:
        st.warning("⚠️ Some tables are missing. Please run `setup_advanced_planning.sql`.")
        print("SCHEMA_VERIFICATION_FAILED")

if __name__ == "__main__":
    check_schema()
