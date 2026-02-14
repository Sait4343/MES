from core.database import DatabaseService
import streamlit as st
import pandas as pd

class WorkerService:
    def __init__(self):
        self.db = DatabaseService()
        self.TABLE = "workers"

    def get_all_workers(self):
        """Fetch all workers with creator details (Manual Join)."""
        try:
            # 1. Fetch all workers raw
            query = self.db.client.table(self.TABLE).select("*").order("full_name")
            res = query.execute()
            workers_data = res.data
            
            if not workers_data:
                return []

            # 2. Fetch Profiles for Name Lookup (Created By / Updated By)
            # We need to look up who created these workers. Creators are still in 'profiles'.
            profiles_query = self.db.client.table("profiles").select("id, full_name, email").execute()
            profiles_data = profiles_query.data
            
            # Create Lookup Map (ID -> Name/Email)
            user_map = {}
            for row in profiles_data:
                uid = row.get('id')
                if uid:
                    user_map[uid] = row.get('full_name') or row.get('email')

            # 3. Map UUIDs to Names manually
            for row in workers_data:
                created_by_id = row.get('created_by')
                updated_by_id = row.get('updated_by')
                
                if created_by_id and created_by_id in user_map:
                    row['created_by_name'] = user_map[created_by_id]
                
                if updated_by_id and updated_by_id in user_map:
                    row['updated_by_name'] = user_map[updated_by_id]
                    
            return workers_data
        except Exception as e:
            st.error(f"Error fetching workers: {e}")
            return []

    def get_operation_types(self):
        """Fetch unique sections from operations_catalog to serve as Operation Types."""
        try:
            res = self.db.client.table("operations_catalog").select("section").execute()
            df = pd.DataFrame(res.data)
            if not df.empty and 'section' in df.columns:
                return sorted(df['section'].dropna().unique().tolist())
            return []
        except Exception as e:
            return []

    def update_worker_profile(self, worker_id, data, current_user_id=None):
        """Update worker details."""
        try:
            if current_user_id:
                data['updated_by'] = current_user_id
            
            return self.db.client.table(self.TABLE).update(data).eq("id", worker_id).execute()
        except Exception as e:
            st.error(f"Error updating worker: {e}")
            return None

    def import_workers(self, df, column_mapping, user_id=None):
        """
        Import/Update workers from Excel into 'workers' table.
        Match by FULL NAME.
        """
        # 1. Separate Multi-Column Mappings
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
        
        # 4. Fetch existing workers for matching
        all_workers = self.get_all_workers() # Now fetches from 'workers' table
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
            
            # Common Data Prep
            worker_data = {}
            if name: worker_data['full_name'] = name
            if 'position' in row: worker_data['position'] = row['position']
            if 'competence' in row: worker_data['competence'] = str(row['competence'])
            if 'comment' in row: worker_data['comment'] = str(row['comment'])
            
            # Handle Multi-Column Operation Types
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
                worker_data['operation_types'] = sorted(list(set(ops_list)))

            # Perform DB Action
            try:
                if name_key and name_key in name_map:
                    # UPDATE
                    if user_id: worker_data['updated_by'] = user_id
                    self.db.client.table(self.TABLE).update(worker_data).eq("id", name_map[name_key]).execute()
                    success += 1
                else:
                    # INSERT
                    if user_id: 
                        worker_data['created_by'] = user_id
                        worker_data['updated_by'] = user_id
                    self.db.client.table(self.TABLE).insert(worker_data).execute()
                    success += 1
                    
            except Exception:
                errors += 1
                
        return success, errors
