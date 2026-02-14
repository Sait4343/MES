import pandas as pd
from core.database import DatabaseService
import streamlit as st

class SectionsService:
    def __init__(self):
        self.db = DatabaseService()
        self.TABLE = "sections"

    def get_all_sections(self):
        """Fetch all sections with user details."""
        try:
            # Join with profiles
            query = self.db.client.table(self.TABLE).select(
                "*, created_by_user:created_by(email, full_name), updated_by_user:updated_by(email, full_name)"
            ).order("name")
            
            res = query.execute()
            df = pd.DataFrame(res.data)
            
            if not df.empty:
                # Flatten creator/updater
                for col in ['created_by_user', 'updated_by_user']:
                    if col in df.columns:
                        df[col.replace('_user', '_name')] = df[col].apply(
                            lambda x: x.get('full_name') or x.get('email') if isinstance(x, dict) else None
                        )
                        # Drop original dict column to keep it clean
                        df.drop(columns=[col], inplace=True)
            return df
        except Exception as e:
            st.error(f"Error fetching sections: {e}")
            return pd.DataFrame()

    def get_operations_by_section(self, section_name):
        """Fetch operations for a specific section."""
        try:
            res = self.db.client.table("operations_catalog").select("*").eq("section", section_name).order("operation_number").execute()
            return pd.DataFrame(res.data)
        except Exception as e:
            # st.error(f"Error fetching section operations: {e}")
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

    def create_section(self, data, user_id=None):
        try:
            if user_id:
                data['created_by'] = user_id
                data['updated_by'] = user_id
                
            self.db.client.table(self.TABLE).insert(data).execute()
            return True, None
        except Exception as e:
            return False, str(e)

    def update_section(self, section_id, data, user_id=None):
        try:
            if user_id:
                data['updated_by'] = user_id
                data['updated_at'] = "now()"
                
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

    def import_sections(self, df, column_mapping, user_id=None):
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
                
                if user_id:
                    clean_row['created_by'] = user_id
                    clean_row['updated_by'] = user_id
                
                if clean_row.get('name'):
                    # Insert (or Upsert if we had ID, but we likely don't)
                    # We'll try insert, if name unique constraint fails -> Error for now or could upsert on name
                    self.db.client.table(self.TABLE).insert(clean_row).execute()
                    success += 1
            except Exception:
                errors += 1
                
        return success, errors
