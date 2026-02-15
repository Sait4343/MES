import sys
import os

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import streamlit as st
import pandas as pd
from io import BytesIO
from auth import require_role
from utils import create_order, fetch_orders
from supabase import create_client

st.set_page_config(page_title="Admin Panel", layout="wide")
require_role(["admin"])

st.title("🛡️ Admin Panel")

tab1, tab2 = st.tabs(["Import Orders", "Export Data"])

with tab1:
    st.header("Import Orders from Excel")
    uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx"])
    
    if uploaded_file is not None:
        try:
            df = pd.read_excel(uploaded_file)
            st.dataframe(df.head())
            
            if st.button("Import Data"):
                success_count = 0
                error_count = 0
                
                with st.spinner("Importing..."):
                    for index, row in df.iterrows():
                        # Basic mapping - adjust based on Excel template
                        order_data = {
                            "order_number": str(row.get("Order Number", "")),
                            "product_name": str(row.get("Product", "")),
                            "article": str(row.get("Article", "")),
                            "quantity": int(row.get("Quantity", 1)),
                            "version": str(row.get("Version", "")),
                            "contractor": str(row.get("Contractor", "")),
                            # Date parsing might be needed here
                            # "start_date": row.get("Start Date"),
                            # "shipping_date": row.get("Shipping Date"),
                            "comment": str(row.get("Comment", ""))
                        }
                        
                        result = create_order(order_data)
                        if result:
                            success_count += 1
                        else:
                            error_count += 1
                            
                st.success(f"Imported {success_count} orders successfully.")
                if error_count > 0:
                    st.warning(f"Failed to import {error_count} orders.")
                    
        except Exception as e:
            st.error(f"Error reading file: {e}")

with tab2:
    st.header("Export Data to Excel")
    
    if st.button("Generate Excel Export"):
        df = fetch_orders()
        
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Orders')
            
        processed_data = output.getvalue()
        
        st.download_button(
            label="Download Excel File",
            data=processed_data,
            file_name="production_orders.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
