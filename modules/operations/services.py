import pandas as pd
from core.database import DatabaseService
import streamlit as st

class OperationsService:
    def __init__(self):
        self.db = DatabaseService()
        self.TABLE = "operations_catalog"

    def get_operations(self):
        """Fetch all operations with user details."""
        try:
            # Join with profiles to get creator and updater info
            # Syntax: numeric columns, normal columns, and joined tables.
            # We use the FK column name to disambiguate the join to profiles table
            query = self.db.client.table(self.TABLE).select(
                "*, created_by_user:profiles!created_by(email, full_name), updated_by_user:profiles!updated_by(email, full_name)"
            ).order("created_at", desc=True)
            
            res = query.execute()
            
            if not res.data:
                return pd.DataFrame()

            # Flatten the response for easier pandas processing
            # created_by_user becomes a dict, we want to extract email/name
            data = []
            for item in res.data:
                row = item.copy()
                
                # Flatten Creator
                creator = row.pop("created_by_user", None)
                if creator:
                    row["created_by_email"] = creator.get("email")
                    row["created_by_name"] = creator.get("full_name")
                
                # Flatten Updater
                updater = row.pop("updated_by_user", None)
                if updater:
                    row["updated_by_email"] = updater.get("email")
                    row["updated_by_name"] = updater.get("full_name")
                    
                data.append(row)
                
            return pd.DataFrame(data)
        except Exception as e:
            st.error(f"Error fetching operations: {e}")
            return pd.DataFrame()

    def create_operation(self, data, user_id=None):
        """Create a single operation."""
        try:
            if user_id:
                data["created_by"] = user_id
                data["updated_by"] = user_id
            
            self.db.client.table(self.TABLE).insert(data).execute()
            return True, None
        except Exception as e:
            return False, str(e)

    def update_operation(self, op_id, data, user_id=None):
        """Update an operation by ID."""
        try:
            if user_id:
                data["updated_by"] = user_id
                
            data["updated_at"] = "now()"
            
            self.db.client.table(self.TABLE).update(data).eq("id", op_id).execute()
            return True, None
        except Exception as e:
            return False, str(e)

    def delete_all_operations(self):
        """Delete ALL operations."""
        try:
            # Delete all rows
            self.db.client.table(self.TABLE).delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
            return True
        except Exception as e:
            st.error(f"Error deleting all operations: {e}")
            return False

    def delete_operation(self, op_id):
        """Delete an operation by ID."""
        try:
            self.db.client.table(self.TABLE).delete().eq("id", op_id).execute()
            return True
        except Exception as e:
            st.error(f"Error deleting operation: {e}")
            return False

    def import_operations(self, df, column_mapping, user_id=None):
        """
        Import operations from a dataframe using a column mapping.
        """
        # 1. Rename columns based on mapping
        rename_map = {v: k for k, v in column_mapping.items() if v}
        df_mapped = df[list(rename_map.keys())].rename(columns=rename_map)
        
        # 2. Add defaults/clean types
        import numpy as np
        
        if 'norm_time' in df_mapped.columns:
            df_mapped['norm_time'] = pd.to_numeric(df_mapped['norm_time'], errors='coerce').fillna(0.0)

        # CRITICAL: Prepare for JSON serialization
        df_mapped = df_mapped.astype(object)
        
        df_mapped = df_mapped.replace({
            np.nan: None, 
            pd.NA: None, 
            float('inf'): None, 
            float('-inf'): None
        })
            
        data = df_mapped.to_dict(orient='records')
        
        if not data:
            return 0, 0
            
        # Add user_id tracking to all records
        if user_id:
            for record in data:
                record["created_by"] = user_id
                record["updated_by"] = user_id
            
        # 3. Batch Insert
        success_count = 0
        error_count = 0
        
        try:
            chunk_size = 100
            for i in range(0, len(data), chunk_size):
                chunk = data[i:i + chunk_size]
                self.db.client.table(self.TABLE).insert(chunk).execute()
                success_count += len(chunk)
        except Exception as e:
            st.error(f"Import error: {e}")
            error_count = len(data)
            
        return success_count, error_count
