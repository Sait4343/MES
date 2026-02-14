import toml
from supabase import create_client

def main():
    try:
        secrets = toml.load(".streamlit/secrets.toml")
        url = secrets["SUPABASE_URL"]
        key = secrets["SUPABASE_KEY"]
        supabase = create_client(url, key)
        
        with open("migration_ops_tracking.sql", "r", encoding="utf-8") as f:
            sql = f.read()
            
        print("Executing migration...")
        
        # Supabase-py doesn't support raw SQL easily without RPC.
        # But we can try to use the REST API to call a function if we had one.
        # Since we don't, and we saw earlier that 'execute_migration.py' failed to run raw SQL
        # because of library limitations, WE MUST ASK THE USER TO RUN IT
        # OR attempt to use a known RPC if one exists.
        
        # Checking if we have a 'exec_sql' RPC (common pattern)
        try:
            supabase.rpc("exec_sql", {"query": sql}).execute()
            print("Migration executed via RPC 'exec_sql'.")
        except Exception as e:
            print(f"RPC execution failed: {e}")
            print("Please execute 'migration_ops_tracking.sql' manually in Supabase SQL Editor.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
