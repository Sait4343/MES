import toml
from supabase import create_client
import sys

def verify():
    try:
        secrets = toml.load(".streamlit/secrets.toml")
        url = secrets["SUPABASE_URL"]
        key = secrets["SUPABASE_KEY"]
        supabase = create_client(url, key)

        print("Verifying if step_name accepts text...")

        # Try to insert a row with a random text step_name
        # We need a valid order_id. Let's list one order first.
        orders = supabase.table("orders").select("id").limit(1).execute()
        
        if not orders.data:
            print("No orders found to test verification.")
            return

        order_id = orders.data[0]['id']
        test_step = "verification_test_step"

        # Attempt insert
        try:
            data = supabase.table("production_steps").insert({
                "order_id": order_id,
                "step_name": test_step,
                "status": "not_started"
            }).execute()
            
            print("Verification SUCCESS: step_name accepts text.")
            
            # Clean up
            supabase.table("production_steps").delete().eq("order_id", order_id).eq("step_name", test_step).execute()
            
        except Exception as e:
            print(f"Verification FAILED: {e}")
            sys.exit(1)

    except Exception as e:
        print(f"Error checking verification: {e}")
        sys.exit(1)

if __name__ == "__main__":
    verify()
