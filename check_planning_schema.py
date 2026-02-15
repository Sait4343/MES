import toml
from supabase import create_client
import sys

def check_schema():
    try:
        secrets = toml.load(".streamlit/secrets.toml")
        url = secrets["SUPABASE_URL"]
        key = secrets["SUPABASE_KEY"]
        supabase = create_client(url, key)

        print("Checking for 'sections' table...")
        try:
            supabase.table("sections").select("id").limit(1).execute()
            print("✅ Table 'sections' exists.")
        except Exception as e:
            print(f"❌ Table 'sections' check failed: {e}")
            return False

        print("Checking for 'operations_catalog' table...")
        try:
            supabase.table("operations_catalog").select("id").limit(1).execute()
            print("✅ Table 'operations_catalog' exists.")
        except Exception as e:
            print(f"❌ Table 'operations_catalog' check failed: {e}")
            return False

        print("Checking for 'order_operations' table...")
        try:
            supabase.table("order_operations").select("id").limit(1).execute()
            print("✅ Table 'order_operations' exists.")
        except Exception as e:
            print(f"❌ Table 'order_operations' check failed: {e}")
            return False

        return True

    except Exception as e:
        print(f"Error connecting to Supabase: {e}")
        return False

if __name__ == "__main__":
    if check_schema():
        print("Schema verification PASSED.")
    else:
        print("Schema verification FAILED. Please run 'setup_advanced_planning.sql'.")
