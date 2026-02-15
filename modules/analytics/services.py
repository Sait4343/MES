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

    def get_planning_data(self):
        """
        Fetch and process data for Planning Dashboard:
        1. Gantt Chart Data (Order Ops with projected times)
        2. Section Workload
        3. Worker Workload
        """
        try:
            # 1. Fetch Data
            ops = self.db.client.table("order_operations").select(
                "*, orders(order_number, product_name), sections(name, capacity_minutes), workers(full_name)"
            ).execute().data
            
            if not ops:
                return pd.DataFrame()
            
            df = pd.DataFrame(ops)
            
            # Flatten
            if 'orders' in df.columns:
                df['Order'] = df['orders'].apply(lambda x: x.get('order_number') if x else '??')
                df['Product'] = df['orders'].apply(lambda x: x.get('product_name') if x else '')
            
            if 'sections' in df.columns:
                df['Section'] = df['sections'].apply(lambda x: x.get('name') if x else 'Unknown')
                df['Section Cap'] = df['sections'].apply(lambda x: x.get('capacity_minutes', 0) if x else 0)
                
            if 'workers' in df.columns:
                df['Worker'] = df['workers'].apply(lambda x: x.get('full_name') if x else 'Unassigned')
            
            # 2. Calculate Gantt Schedule
            # We assume 'planned_date' is the start day.
            # We assume operations within an order are sequential based on 'sort_order'.
            # We project Start/End time based on 'total_estimated_time' (minutes).
            # Start of day: 09:00 (for simulation)
            
            df['start_time'] = pd.NaT
            df['end_time'] = pd.NaT
            
            # Sort by Order, Date, SortOrder
            df = df.sort_values(by=['order_id', 'planned_date', 'sort_order'])
            
            # Logic: 
            # For each order:
            #   First op starts at Planned Date 09:00
            #   Next op starts at Previous Op End Time
            #   (Simplification: ignoring non-working hours/breaks for MVP)
            
            for order_id, group in df.groupby('order_id'):
                current_time = None
                
                for idx, row in group.iterrows():
                    p_date = pd.to_datetime(row.get('planned_date')) if row.get('planned_date') else pd.Timestamp.now().normalize()
                    duration_min = row.get('total_estimated_time', 0) or 0
                    
                    if current_time is None:
                        # Start of Order processing (First step)
                        # Default to 09:00 of planned date
                        current_time = p_date.replace(hour=9, minute=0)
                    
                    # If current op has a later planned date, jump to it? 
                    # For now, simplistic chaining.
                    
                    start = current_time
                    end = start + timedelta(minutes=float(duration_min))
                    
                    df.at[idx, 'start_time'] = start
                    df.at[idx, 'end_time'] = end
                    
                    current_time = end
            
            # 3. Workload Aggregations (for Current Week?)
            # Let's just aggregate the whole fetched dataset for now, or filter by 'planned_date' in view.
            
            return df
            
        except Exception as e:
            st.error(f"Error calculating planning data: {e}")
            return pd.DataFrame()

    def get_section_metrics_summary(self, target_date=None):
        """
        Calculate metrics for each section for a specific date (default: today).
        Returns: List of dicts with section metrics.
        """
        if target_date is None:
            target_date = datetime.now().date()
        
        try:
            # Fetch all sections
            sections_res = self.db.client.table("sections").select("id, name, capacity_minutes").execute()
            sections = sections_res.data
            
            if not sections:
                return []
            
            # Fetch operations for the target date
            # We check operations where scheduled_start_at is on target_date
            start_of_day = datetime.combine(target_date, datetime.min.time())
            end_of_day = datetime.combine(target_date, datetime.max.time())
            
            ops_res = self.db.client.table("order_operations").select(
                "section_id, assigned_worker_id, norm_time_per_unit, quantity, scheduled_start_at, scheduled_end_at"
            ).gte("scheduled_start_at", start_of_day.isoformat()).lte("scheduled_start_at", end_of_day.isoformat()).execute()
            
            ops_df = pd.DataFrame(ops_res.data) if ops_res.data else pd.DataFrame()
            
            metrics = []
            for section in sections:
                sec_id = section['id']
                sec_name = section['name']
                capacity = section.get('capacity_minutes', 480)
                
                # Filter ops for this section
                if not ops_df.empty and 'section_id' in ops_df.columns:
                    sec_ops = ops_df[ops_df['section_id'] == sec_id]
                else:
                    sec_ops = pd.DataFrame()
                
                # Calculate scheduled minutes
                if not sec_ops.empty:
                    sec_ops['duration'] = sec_ops['norm_time_per_unit'] * sec_ops['quantity']
                    scheduled_mins = sec_ops['duration'].sum()
                    num_operations = len(sec_ops)
                    num_workers = sec_ops['assigned_worker_id'].nunique()
                else:
                    scheduled_mins = 0
                    num_operations = 0
                    num_workers = 0
                
                # Utilization %
                utilization = round((scheduled_mins / capacity * 100), 1) if capacity > 0 else 0
                
                metrics.append({
                    'section_id': sec_id,
                    'section_name': sec_name,
                    'capacity_minutes': capacity,
                    'scheduled_minutes': scheduled_mins,
                    'utilization_percent': utilization,
                    'num_operations': num_operations,
                    'num_workers': num_workers
                })
            
            return metrics
            
        except Exception as e:
            st.error(f"Error calculating section metrics: {e}")
            return []

    def get_section_weekly_trend(self, section_id, num_days=7):
        """
        Get daily utilization trend for a section for the next N days.
        Returns: DataFrame with columns: date, utilization_percent
        """
        try:
            # Get section capacity
            sec_res = self.db.client.table("sections").select("capacity_minutes").eq("id", section_id).execute()
            if not sec_res.data:
                return pd.DataFrame()
            
            capacity = sec_res.data[0].get('capacity_minutes', 480)
            
            # Date range
            start_date = datetime.now().date()
            dates = [start_date + timedelta(days=i) for i in range(num_days)]
            
            trend_data = []
            
            for date in dates:
                start_of_day = datetime.combine(date, datetime.min.time())
                end_of_day = datetime.combine(date, datetime.max.time())
                
                # Fetch operations for this section on this date
                ops_res = self.db.client.table("order_operations").select(
                    "norm_time_per_unit, quantity"
                ).eq("section_id", section_id).gte("scheduled_start_at", start_of_day.isoformat()).lte("scheduled_start_at", end_of_day.isoformat()).execute()
                
                ops_df = pd.DataFrame(ops_res.data) if ops_res.data else pd.DataFrame()
                
                if not ops_df.empty:
                    ops_df['duration'] = ops_df['norm_time_per_unit'] * ops_df['quantity']
                    scheduled_mins = ops_df['duration'].sum()
                else:
                    scheduled_mins = 0
                
                utilization = round((scheduled_mins / capacity * 100), 1) if capacity > 0 else 0
                
                trend_data.append({
                    'date': date,
                    'utilization_percent': utilization,
                    'scheduled_minutes': scheduled_mins
                })
            
            return pd.DataFrame(trend_data)
            
        except Exception as e:
            st.error(f"Error calculating weekly trend: {e}")
            return pd.DataFrame()
