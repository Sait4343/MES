from core.database import DatabaseService
import streamlit as st

class WorkerService:
    def __init__(self):
        self.db = DatabaseService()

    def get_all_workers(self):
        """Fetch all user profiles."""
        try:
            return self.db.client.table("profiles").select("*").order("full_name").execute().data
        except Exception as e:
            st.error(f"Error fetching workers: {e}")
            return []

    def get_operation_types(self):
        """Fetch unique sections from operations_catalog to serve as Operation Types."""
        try:
            # We want unique sections. 
            # Supabase select supports simple distinct? 
            # Or we fetch all and distinct in Pandas (easier for small datasets).
            res = self.db.client.table("operations_catalog").select("section").execute()
            df = pd.DataFrame(res.data)
            if not df.empty and 'section' in df.columns:
                return sorted(df['section'].dropna().unique().tolist())
            return []
        except Exception as e:
            # st.error(f"Error fetching operation types: {e}")
            return []

    def update_worker_role(self, user_id, new_role):
        """Update a user's role (Admin only)."""
        try:
            return self.db.client.table("profiles").update({"role": new_role}).eq("id", user_id).execute()
        except Exception as e:
            st.error(f"Error updating role: {e}")
            return None

    def update_worker_profile(self, user_id, data):
        """Update worker profile details (Position, Competence, Op Types)."""
        try:
            return self.db.client.table("profiles").update(data).eq("id", user_id).execute()
        except Exception as e:
            st.error(f"Error updating profile: {e}")
            return None

    def import_workers(self, df, column_mapping):
        """
        Import/Update workers from Excel.
        Match by EMAIL. If email found, update fields.
        column_mapping: dict where keys are DB fields, values are Excel headers (or list of headers for multi-select)
        """
        # 1. Separate Multi-Column Mappings (like operation_types)
        multi_col_mappings = {}
        single_col_mapping = {}
        
        for k, v in column_mapping.items():
            if isinstance(v, list):
                multi_col_mappings[k] = v
            else:
                single_col_mapping[k] = v

        # 2. Rename single columns
        rename_map = {v: k for k, v in single_col_mapping.items() if v}
        df_mapped = df[list(rename_map.keys())].rename(columns=rename_map)
        
        # 3. Prepare data dict
        data = df_mapped.to_dict(orient='records')
        if not data:
            return 0, 0
            
        success = 0
        errors = 0
        
        # 4. Fetch existing for matching
        all_workers = self.get_all_workers()
        email_map = {w['email']: w['id'] for w in all_workers if w.get('email')}
        
        for i, row in enumerate(data):
            # Access original row for multi-col data (using index i, assuming data order preserved)
            original_row = df.iloc[i]
            
            email = row.get('email')
            if email and email in email_map:
                # Update existing
                try:
                    # Clean up data
                    update_data = {}
                    if 'full_name' in row: update_data['full_name'] = row['full_name']
                    if 'position' in row: update_data['position'] = row['position']
                    if 'competence' in row: update_data['competence'] = str(row['competence'])
                    
                    # Handle Multi-Column Operation Types
                    ops_list = []
                    
                    # 1. From single mapped column (backwards compatibility or mixed use)
                    if 'operation_types' in row and isinstance(row['operation_types'], str):
                         ops_list.extend([x.strip() for x in row['operation_types'].split(',')])
                    
                    # 2. From multi-mapped columns
                    if 'operation_types' in multi_col_mappings:
                        cols = multi_col_mappings['operation_types']
                        for col in cols:
                            val = original_row.get(col)
                            if pd.notna(val):
                                # If value is string, split by comma, else just add
                                str_val = str(val).strip()
                                if str_val:
                                    ops_list.extend([x.strip() for x in str_val.split(',')])
                    
                    if ops_list:
                        # Dedup and clean
                        update_data['operation_types'] = sorted(list(set(ops_list)))
                    
                    if update_data:
                        self.db.client.table("profiles").update(update_data).eq("id", email_map[email]).execute()
                        success += 1
                except Exception:
                    errors += 1
            else:
                # Email not found
                errors += 1
                
        return success, errors
