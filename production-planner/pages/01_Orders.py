import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode
from utils import fetch_orders, update_order, update_step_status
from auth import require_auth, require_role

# Page Configuration
st.set_page_config(page_title="Orders | Production Planner", layout="wide")

# Authentication
user = require_auth()
role = st.session_state.get("role", "worker")

st.title("📦 Production Orders")

# Fetch Data
if "orders_data" not in st.session_state:
    st.session_state.orders_data = fetch_orders()

# Reload Button
if st.button("🔄 Reload Data"):
    st.session_state.orders_data = fetch_orders()
    st.rerun()

df = st.session_state.orders_data

if df.empty:
    st.info("No orders found.")
    st.stop()

# Configure AgGrid
gb = GridOptionsBuilder.from_dataframe(df)
gb.configure_pagination(paginationAutoPageSize=False, paginationPageSize=20)
gb.configure_side_bar()
gb.configure_default_column(groupable=True, value=True, enableRowGroup=True, aggFunc="sum", editable=True)

# Field Specific Configuration
# Read-only fields
gb.configure_column("id", hide=True)
gb.configure_column("created_at", hide=True)
gb.configure_column("updated_at", hide=True)

# Dropdowns for Steps
step_columns = [col for col in df.columns if col.startswith("step_")]
for col in step_columns:
    gb.configure_column(col, cellEditor="agSelectCellEditor", cellEditorParams={"values": ["not_started", "in_progress", "done", "problem"]})

# Role-based constraints
if role == "worker":
    # Workers can only edit step status columns
    non_step_columns = [col for col in df.columns if not col.startswith("step_")]
    for col in non_step_columns:
        gb.configure_column(col, editable=False)

gridOptions = gb.build()

st.markdown(f"**Role:** {role.capitalize()} | **Mode:** {'Edit Steps' if role == 'worker' else 'Edit All'}")

grid_response = AgGrid(
    df,
    gridOptions=gridOptions,
    data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
    update_mode=GridUpdateMode.MANUAL,
    fit_columns_on_grid_load=False,
    height=600,
    width='100%',
    enable_enterprise_modules=False
)

# Save Changes Logic
if st.button("💾 Save Changes"):
    updated_df = pd.DataFrame(grid_response['data'])
    
    # Compare with original to find changes
    # This is a naive implementation; for production, we'd want row-level diffs
    # iterating through updated_df and calling update APIs is safer
    
    original_df = st.session_state.orders_data
    
    with st.spinner("Saving changes..."):
        # Iterate rows
        changes_count = 0
        for index, row in updated_df.iterrows():
            order_id = row['id']
            original_row = original_df[original_df['id'] == order_id].iloc[0]
            
            # Check for core field changes (Admin/Manager only)
            if role in ['admin', 'manager']:
                core_updates = {}
                core_fields = ['order_number', 'product_name', 'article', 'quantity', 'version', 'contractor', 'start_date', 'shipping_date', 'comment']
                
                for field in core_fields:
                    if str(row[field]) != str(original_row[field]):
                        # Simple value check, date handling might need parsing
                         core_updates[field] = row[field]
                
                if core_updates:
                    update_order(order_id, core_updates)
                    changes_count += 1
            
            # Check for step status changes (All users)
            for col in step_columns:
                step_name = col.replace("step_", "")
                if row[col] != original_row[col]:
                    update_step_status(order_id, step_name, row[col], user.id if row[col] == 'in_progress' else None)
                    changes_count += 1

        st.success(f"Saved {changes_count} changes!")
        # Reload fresh data
        st.session_state.orders_data = fetch_orders()
        st.rerun()
