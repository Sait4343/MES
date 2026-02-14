import pandas as pd
from core.database import DatabaseService
import streamlit as st

class SectionsService:
    def __init__(self):
        self.db = DatabaseService()
        self.TABLE = "sections"

    def get_all_sections(self):
        """Fetch all sections."""
        try:
            res = self.db.client.table(self.TABLE).select("*").order("name").execute()
            return pd.DataFrame(res.data)
        except Exception as e:
            st.error(f"Error fetching sections: {e}")
            return pd.DataFrame()

    def get_operation_types_source(self):
        """Fetch unique operation types (sections) from operations_catalog for the dropdown."""
        try:
            res = self.db.client.table("operations_catalog").select("section").execute()
            df = pd.DataFrame(res.data)
            if not df.empty and 'section' in df.columns:
                return sorted(df['section'].dropna().unique().tolist())
            return []
        except Exception as e:
            # st.error(f"Error fetching source op types: {e}")
            return []

    def create_section(self, data):
        try:
            self.db.client.table(self.TABLE).insert(data).execute()
            return True, None
        except Exception as e:
            return False, str(e)

    def update_section(self, section_id, data):
        try:
            self.db.client.table(self.TABLE).update(data).eq("id", section_id).execute()
            return True, None
        except Exception as e:
            return False, str(e)

    def delete_section(self, section_id):
        try:
            self.db.client.table(self.TABLE).delete().eq("id", section_id).execute()
            return True
        except Exception as e:
            st.error(f"Error deleting section: {e}")
            return False

    def import_sections(self, df, column_mapping):
        """
        Import sections from Excel.
        """
        # 1. Rename
        rename_map = {v: k for k, v in column_mapping.items() if v}
        df_mapped = df[list(rename_map.keys())].rename(columns=rename_map)
        
        data = df_mapped.to_dict(orient='records')
        if not data:
            return 0, 0
            
        success = 0
        errors = 0
        
        for row in data:
            try:
                # Clean
                clean_row = {}
                if 'name' in row: clean_row['name'] = str(row['name']).strip()
                if 'capacity_minutes' in row: 
                    clean_row['capacity_minutes'] = pd.to_numeric(row['capacity_minutes'], errors='coerce') or 0
                if 'description' in row: clean_row['description'] = str(row['description'])
                if 'operation_types' in row and isinstance(row['operation_types'], str):
                     clean_row['operation_types'] = [x.strip() for x in row['operation_types'].split(',')]
                
                if clean_row.get('name'):
                    # Insert (or Upsert if we had ID, but we likely don't)
                    # We'll try insert, if name unique constraint fails -> Error for now or could upsert on name
                    self.db.client.table(self.TABLE).insert(clean_row).execute()
                    success += 1
            except Exception:
                errors += 1
                
        return success, errors
