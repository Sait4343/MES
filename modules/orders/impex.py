import pandas as pd
import io
from core.database import DatabaseService
import streamlit as st

class ImpexService:
    def __init__(self):
        self.db = DatabaseService()
        self.required_columns = ["order_number", "product_name", "quantity"]
        
        # Mapping Ukrainian headers to DB columns
        # Structure: { "Excel Header": "db_column" }
        self.column_mapping = {
            "Номер замовлення": "order_number",
            "Order #": "order_number",
            
            "Назва виробу": "product_name",
            "Product": "product_name",
            "Item": "product_name",
            
            "Артикул": "article",
            "Article": "article",
            
            "Кількість": "quantity",
            "Qty": "quantity",
            "Quantity": "quantity",
            
            "Контрагент": "contractor",
            "Contractor": "contractor",
            "Customer": "contractor",
            
            "Дата відвантаження": "shipping_date",
            "Ship Date": "shipping_date",
            "Deadline": "shipping_date",
            
            "Дата початку": "start_date",
            "Start Date": "start_date",

            "Дата підготовки": "preparation_date",
            "Prep Date": "preparation_date",
            
            "Коментар": "comment",
            "Comment": "comment",
            "Notes": "comment"
        }

    def get_field_aliases(self, db_field):
        """Return list of possible Excel headers for a given DB field."""
        return [k for k, v in self.column_mapping.items() if v == db_field]

    def import_orders_from_df(self, df, column_mapping):
        """
        Import orders from DataFrame with dynamic column mapping.
        """
        # 1. Rename columns based on mapping
        rename_map = {v: k for k, v in column_mapping.items() if v and v != '(Пропустити)'}
        # Invert mapping: UI maps DB_COL -> EXCEL_HEADER (v). 
        # We need EXCEL_HEADER -> DB_COL for renaming.
        rename_map = {v: k for k, v in column_mapping.items() if v and v != "(Пропустити)"}
        
        # Select only mapped columns
        try:
            df_mapped = df[list(rename_map.keys())].rename(columns=rename_map)
        except KeyError as e:
            return 0, f"Missing columns in Excel: {e}"
            
        orders_data = df_mapped.to_dict(orient='records')
        
        success_count = 0
        fail_count = 0
        
        for order in orders_data:
            try:
                # Cleaning & Validation
                clean_order = {}
                
                # Helper to safely get and clean
                def get_val(key):
                    if key in order and pd.notna(order[key]):
                        return order[key]
                    return None

                # Mandatory fields
                order_number = get_val("order_number")
                product_name = get_val("product_name")
                quantity = get_val("quantity")
                
                if not order_number or not product_name:
                    fail_count += 1
                    continue
                    
                clean_order["order_number"] = str(order_number).strip()
                clean_order["product_name"] = str(product_name).strip()
                
                # Quantity
                try:
                    clean_order["quantity"] = int(quantity) if quantity else 1
                except:
                     clean_order["quantity"] = 1
                     
                # Optional fields
                if get_val("article"): clean_order["article"] = str(get_val("article")).strip()
                if get_val("contractor"): clean_order["contractor"] = str(get_val("contractor")).strip()
                if get_val("comment"): clean_order["comment"] = str(get_val("comment")).strip()
                
                # Dates
                for date_field in ["shipping_date", "start_date", "preparation_date"]:
                    val = get_val(date_field)
                    if val:
                        try:
                            clean_order[date_field] = pd.to_datetime(val).strftime('%Y-%m-%d')
                        except:
                            pass # Ignore invalid date

                # Insert
                # Upsert (Insert or Update based on order_number)
                self.db.client.table("orders").upsert(
                    clean_order, 
                    on_conflict="order_number"
                ).execute()
                success_count += 1
                
            except Exception as e:
                st.error(f"Row Error: {e}")
                fail_count += 1
                
        return success_count, fail_count

    def export_orders(self):
        """Export orders to Excel bytes."""
        try:
            # Fetch data
            data = self.db.client.table("orders").select("*").order("created_at", desc=True).execute().data
            
            if not data:
                return None
                
            df = pd.DataFrame(data)
            
            # Select and Rename columns for export
            export_cols = ["order_number", "product_name", "article", "quantity", "contractor", "shipping_date", "comment", "created_at"]
            
            # Filter existing columns only
            valid_cols = [c for c in export_cols if c in df.columns]
            df = df[valid_cols]
            
            df.rename(columns={
                "order_number": "Номер замовлення",
                "product_name": "Назва виробу",
                "article": "Артикул",
                "quantity": "Кількість",
                "contractor": "Контрагент",
                "shipping_date": "Дата відвантаження",
                "comment": "Коментар",
                "created_at": "Дата створення"
            }, inplace=True)
            
            # Convert to Bytes
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Orders')
                
            return output.getvalue()
            
        except Exception as e:
            st.error(f"Error exporting: {e}")
            return None
