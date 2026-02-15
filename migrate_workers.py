"""
Migration script to fix workers table relationship
"""
import os
from supabase import create_client

# Read SQL file
with open('fix_workers_relationship.sql', 'r', encoding='utf-8') as f:
    sql_script = f.read()

# Initialize Supabase
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_KEY")  # Need service key for DDL operations

if not url or not key:
    print("❌ Error: SUPABASE_URL and SUPABASE_SERVICE_KEY must be set")
    print("\nSet them in your environment or .env file:")
    print("  SUPABASE_URL=https://your-project.supabase.co")
    print("  SUPABASE_SERVICE_KEY=your-service-role-key")
    exit(1)

print("🔄 Connecting to Supabase...")
supabase = create_client(url, key)

try:
    print("🚀 Executing migration...")
    # Execute the SQL script
    # Note: supabase-py doesn't have direct SQL execution for DDL
    # We need to use the REST API or PostgREST's RPC function
    
    # Option 1: Use rpc if you have a custom function
    # Option 2: Use requests to call PostgREST directly
    # Option 3: Tell user to run via Supabase Dashboard
    
    print("\n⚠️  The Python Supabase client doesn't support DDL operations directly.")
    print("\n📋 Please run this migration manually via Supabase Dashboard:")
    print("\n1. Go to: https://supabase.com/dashboard/project/YOUR_PROJECT/sql")
    print("2. Open the SQL Editor")
    print("3. Paste the contents of 'fix_workers_relationship.sql'")
    print("4. Click 'RUN' to execute")
    print("\n✅ After running, refresh your Streamlit app")
    
except Exception as e:
    print(f"❌ Error: {e}")
    exit(1)
