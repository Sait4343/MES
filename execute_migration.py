import toml
import os
from supabase import create_client

def main():
    try:
        # Load secrets
        secrets = toml.load(".streamlit/secrets.toml")
        url = secrets["SUPABASE_URL"]
        key = secrets["SUPABASE_KEY"]
        
        # Connect
        print(f"Connecting to Supabase: {url}")
        supabase = create_client(url, key)
        
        # Read SQL
        with open("fix_step_name_error.sql", "r", encoding="utf-8") as f:
            sql = f.read()
            
        print("Executing SQL migration...")
        
        # We need to split the SQL into statements if the client doesn't support multiple
        # But for PL/pgSQL blocks (BEGIN...COMMIT), we often need a single execution or RPC.
        # Supabase-py 'rpc' calls a stored procedure.
        # 'execute_sql' isn't standard in supabase-py unless extended. 
        # Standard supabase-py interacts with PostgREST.
        
        # Fallback: We can't easily execute raw SQL via PostgREST without a helper function.
        # However, we can try to use a predefined 'exec_sql' function if it exists on the server
        # (check core/database.py or previous migrations - usually via `postgres` extension or a custom RPC function).
        
        # Optimization: Since we don't have a known 'exec_sql' RPC, we will try to rely on 'psycopg2' if installed,
        # or use the `supabase-mcp-server` which failed earlier (but maybe due to token?).
        
        # If psycopg2 is not available, we are stuck unless we have a 'exec_sql' RPC.
        # Let's try to define a 'exec_sql' function first via the dashboard (User action) OR assume one exists.
        # But wait, I can try to use `rpc` if I had one.
        
        # Let's try 'psycopg2' - it's a common dependency.
        try:
            import psycopg2
            # We need a connection string. Supabase provides one in Settings -> Database.
            # Usually: postgresql://postgres:[PASSWORD]@db.[PROJECT_REF].supabase.co:5432/postgres
            # We only have API URL/Key. We CANNOT derive the connection string password from the Key.
            
            print("Cannot use psycopg2 without DB Password.")
        except ImportError:
            pass
            
        print("ATTENTION: Please execute the 'fix_step_name_error.sql' contents in your Supabase SQL Editor manually.")
        print("Printing SQL for convenience:")
        print("-" * 20)
        print(sql)
        print("-" * 20)

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
