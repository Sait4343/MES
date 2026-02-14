from core.database import DatabaseService

class DashboardService:
    def __init__(self):
        self.db = DatabaseService()

    def get_stats(self):
        """Fetch high-level statistics."""
        try:
            # Total Orders
            total_orders = self.db.client.table("orders").select("*", count="exact").execute().count
            
            # Active Production Steps (status = in_progress)
            active_steps = self.db.client.table("production_steps").select("*", count="exact").eq("status", "in_progress").execute().count
            
            # Completed Orders (assuming we can infer this or add a status field later)
            # For now, let's just count total orders as a placeholder or add a 'status' to orders table later.
            # Let's count 'done' steps for now as a proxy for activity.
            completed_steps = self.db.client.table("production_steps").select("*", count="exact").eq("status", "done").execute().count

            return {
                "total_orders": total_orders,
                "active_steps": active_steps,
                "completed_steps": completed_steps
            }
        except Exception as e:
            return {
                "total_orders": 0,
                "active_steps": 0,
                "completed_steps": 0,
                "error": str(e)
            }
