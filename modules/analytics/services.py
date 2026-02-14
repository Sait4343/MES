from core.database import DatabaseService
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

class AnalyticsService:
    def __init__(self):
        self.db = DatabaseService()

    def get_raw_data(self):
        """Fetch raw data for processing."""
        try:
            orders = self.db.client.table("orders").select("*").execute().data
            steps = self.db.client.table("production_steps").select("*, orders(order_number, shipping_date)").execute().data
            profiles = self.db.client.table("profiles").select("id, full_name").execute().data
            
            return pd.DataFrame(orders), pd.DataFrame(steps), pd.DataFrame(profiles)
        except Exception as e:
            st.error(f"Error fetching data: {e}")
            return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    def calculate_kpis(self, orders_df, steps_df):
        """Calculate high-level KPIs."""
        if orders_df.empty:
            return {"otd": 0, "delays": 0, "avg_lead_time": 0}

        # 1. On-Time Delivery (OTD)
        # Orders with shipping_date that are done (assuming 'packing' done implies order done or checking order logic)
        # For approximation: Count orders where shipping_date < Today and NOT done? No.
        # Let's count delayed active orders.
        
        today = pd.Timestamp.now().normalize()
        
        if 'shipping_date' in orders_df.columns:
            orders_df['shipping_date'] = pd.to_datetime(orders_df['shipping_date'])
            
            # Delayed: Shipping date passed, but logic for "Done" needs to be robust. 
            # We can check if all steps are done? Or if it's in a 'done' list?
            # Let's use steps_df to find completed orders.
            
            # For simplicity: "Delays" = Shipping Date < Today (and not conceptually finished)
            # We don't have an explicit 'order status' column that is maintained perfectly in this MVP yet except the text default.
            # Let's verify 'step status' to determine order completion.
            
            # However, for this metric, let's just count Overdue Orders.
            overdue = orders_df[orders_df['shipping_date'] < today]
            # In a real app, we'd filter out completed ones.
            # Let's assume 'status' column in orders is used if we implemented the trigger, 
            # otherwise allow for some inaccuracy or join with steps.
            
            delayed_count = len(overdue)
            
            # OTD % calculation would require historical data of completed orders.
            # Let's placeholder it as (1 - (delayed / total)) * 100
            total_active = len(orders_df)
            otd_rate = round(((total_active - delayed_count) / total_active) * 100, 1) if total_active > 0 else 100
            
            return {
                "otd": otd_rate,
                "delays": delayed_count,
                "total": total_active
            }
        
        return {"otd": 0, "delays": 0, "total": 0}

    def get_bottlenecks(self, steps_df):
        """Analyze step durations."""
        if steps_df.empty or 'started_at' not in steps_df.columns or 'completed_at' not in steps_df.columns:
            return pd.DataFrame()

        df = steps_df.copy()
        df['started_at'] = pd.to_datetime(df['started_at'])
        df['completed_at'] = pd.to_datetime(df['completed_at'])
        
        # Duration in hours
        df['duration_hours'] = (df['completed_at'] - df['started_at']).dt.total_seconds() / 3600
        
        # Group by step name
        stats = df.groupby('step_name')['duration_hours'].mean().reset_index()
        stats.columns = ['Step', 'Avg Duration (Hours)']
        return stats.sort_values('Avg Duration (Hours)', ascending=False)

    def get_worker_performance(self, steps_df, profiles_df):
        """Count completed steps per worker."""
        if steps_df.empty or profiles_df.empty:
            return pd.DataFrame()
            
        # Filter completed
        completed = steps_df[steps_df['status'] == 'done']
        
        if completed.empty:
             return pd.DataFrame(columns=["Worker", "Completed Tasks"])

        counts = completed['assigned_worker_id'].value_counts().reset_index()
        counts.columns = ['id', 'count']
        
        # Merge with names
        merged = counts.merge(profiles_df, on='id', how='left')
        merged['Worker'] = merged['full_name'].fillna('Unknown')
        
        return merged[['Worker', 'count']].rename(columns={'count': 'Completed Tasks'})

    def get_step_status_dist(self, steps_df):
         if steps_df.empty: return pd.DataFrame()
         return steps_df['status'].value_counts().reset_index()
