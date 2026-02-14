import pandas as pd
from core.database import DatabaseService
import streamlit as st

class OperationsService:
    def __init__(self):
        self.db = DatabaseService()
        self.TABLE = "operations_catalog"

    def get_operations(self):
        """Fetch all operations."""
        try:
            res = self.db.client.table(self.TABLE).select("*").order("created_at", desc=True).execute()
            return pd.DataFrame(res.data)
        except Exception as e:
            st.error(f"Error fetching operations: {e}")
            return pd.DataFrame()

    def delete_operation(self, op_id):
        """Delete an operation by ID."""
        try:
            self.db.client.table(self.TABLE).delete().eq("id", op_id).execute()
            return True
        except Exception as e:
            st.error(f"Error deleting operation: {e}")
            return False

    def import_operations(self, df, column_mapping):
        """
        Import operations from a dataframe using a column mapping.
        
        column_mapping: dict where key = DB_FIELD, value = EXCEL_COLUMN_NAME
        """
        # 1. Rename columns based on mapping
        # Invert mapping to rename: {ExcelCol: DbCol}
        rename_map = {v: k for k, v in column_mapping.items() if v}
        
        # Filter only columns we mapped
        df_mapped = df[list(rename_map.keys())].rename(columns=rename_map)
        
        # 2. Add defaults/clean types
        if 'norm_time' in df_mapped.columns:
            df_mapped['norm_time'] = pd.to_numeric(df_mapped['norm_time'], errors='coerce').fillna(0)
            
        data = df_mapped.to_dict(orient='records')
        
        if not data:
            return 0, 0
            
        # 3. Batch Insert
        success_count = 0
        error_count = 0
        
        # Supabase allows bulk insert, but let's do chunks if large, 
        # or simple try/except for now. 
        # Using upsert requires unique constraints, we'll just insert for now as duplicates might be allowed or handled later.
        
        try:
            # Chunking because Supabase has payload limits
            chunk_size = 100
            for i in range(0, len(data), chunk_size):
                chunk = data[i:i + chunk_size]
                self.db.client.table(self.TABLE).insert(chunk).execute()
                success_count += len(chunk)
        except Exception as e:
            st.error(f"Import error: {e}")
            error_count = len(data) # conservatively assume all failed in that chunk logic context
            
        return success_count, error_count
