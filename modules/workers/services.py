from core.database import DatabaseService
import streamlit as st

class WorkerService:
    def __init__(self):
        self.db = DatabaseService()

    def get_all_workers(self):
        """Fetch all user profiles with creator details (Manual Join)."""
        try:
            # 1. Fetch all profiles raw
            query = self.db.client.table("profiles").select("*").order("full_name")
            res = query.execute()
            data = res.data
            
            if not data:
                return []

            # 2. Create Lookup Map (ID -> Name/Email)
            user_map = {}
            for row in data:
                uid = row.get('id')
                if uid:
                    user_map[uid] = row.get('full_name') or row.get('email')

            # 3. Map UUIDs to Names manually
            for row in data:
                created_by_id = row.get('created_by')
                updated_by_id = row.get('updated_by')
                
                if created_by_id and created_by_id in user_map:
                    row['created_by_name'] = user_map[created_by_id]
                
                if updated_by_id and updated_by_id in user_map:
                    row['updated_by_name'] = user_map[updated_by_id]
                    
            return data
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

    def update_worker_profile(self, user_id, data, current_user_id=None):
        """Update worker profile details (Position, Competence, Op Types)."""
        try:
            if current_user_id:
                data['updated_by'] = current_user_id
            
            return self.db.client.table("profiles").update(data).eq("id", user_id).execute()
        except Exception as e:
            st.error(f"Error updating profile: {e}")
            return None

    def import_workers(self, df, column_mapping, user_id=None):
        """
        Import/Update workers from Excel.
        Match by FULL NAME. If name found, update fields.
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
        # Map Clean Name -> ID
        name_map = {}
        for w in all_workers:
            nm = w.get('full_name')
            if nm:
                name_map[str(nm).strip().lower()] = w['id']
        
        for i, row in enumerate(data):
            # Access original row for multi-col data
            original_row = df.iloc[i]
            
            name = str(row.get('full_name', '')).strip()
            name_key = name.lower()
            
            if name_key and name_key in name_map:
                # Update existing
                try:
                    # Clean up data
                    update_data = {}
                    if 'position' in row: update_data['position'] = row['position']
                    if 'competence' in row: update_data['competence'] = str(row['competence'])
                    if 'comment' in row: update_data['comment'] = str(row['comment'])
                    
                    if user_id:
                        update_data['updated_by'] = user_id
                    
                    # Handle Multi-Column Operation Types (Shared Logic)
                    ops_list = []
                    # 1. From single mapped column
                    if 'operation_types' in row and isinstance(row['operation_types'], str):
                         ops_list.extend([x.strip() for x in row['operation_types'].split(',')])
                    # 2. From multi-mapped columns
                    if 'operation_types' in multi_col_mappings:
                        cols = multi_col_mappings['operation_types']
                        for col in cols:
                            val = original_row.get(col)
                            if pd.notna(val):
                                str_val = str(val).strip()
                                if str_val:
                                    ops_list.extend([x.strip() for x in str_val.split(',')])
                    
                    if ops_list:
                        update_data['operation_types'] = sorted(list(set(ops_list)))
                    
                    if update_data:
                        self.db.client.table("profiles").update(update_data).eq("id", name_map[name_key]).execute()
                        success += 1
                except Exception:
                    errors += 1
            else:
                # Create NEW Worker (Offline Profile)
                try:
                    new_worker = {
                        "full_name": name,
                        "role": "worker" # Default role
                    }
                    if 'position' in row: new_worker['position'] = row['position']
                    if 'competence' in row: new_worker['competence'] = str(row['competence'])
                    if 'comment' in row: new_worker['comment'] = str(row['comment'])
                    
                    if user_id:
                        new_worker['created_by'] = user_id
                        new_worker['updated_by'] = user_id

                    # Handle Multi-Column Operation Types (Copy-Paste Logic for now, could be refactored)
                    ops_list = []
                    if 'operation_types' in row and isinstance(row['operation_types'], str):
                         ops_list.extend([x.strip() for x in row['operation_types'].split(',')])
                    if 'operation_types' in multi_col_mappings:
                        cols = multi_col_mappings['operation_types']
                        for col in cols:
                            val = original_row.get(col)
                            if pd.notna(val):
                                str_val = str(val).strip()
                                if str_val:
                                    ops_list.extend([x.strip() for x in str_val.split(',')])
                    
                    if ops_list:
                        new_worker['operation_types'] = sorted(list(set(ops_list)))

                    # Insert
                    self.db.client.table("profiles").insert(new_worker).execute()
                    success += 1
                    
                except Exception as e:
                    # st.error(f"Create error: {e}")
                    errors += 1
                
        return success, errors

    def delete_worker(self, user_id):
        """Delete a worker from profiles."""
        try:
            self.db.client.table("profiles").delete().eq("id", user_id).execute()
            return True
        except Exception as e:
            st.error(f"Error deleting worker: {e}")
            return False
