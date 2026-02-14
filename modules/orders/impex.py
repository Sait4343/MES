import pandas as pd
import io
from core.database import DatabaseService
import streamlit as st

class ImpexService:
    def __init__(self):
        self.db = DatabaseService()
        self.required_columns = ["order_number", "product_name", "quantity"]
        
        # Mapping Ukrainian headers to DB columns
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
            
            "Коментар": "comment",
            "Comment": "comment",
            "Notes": "comment"
        }

    def parse_excel(self, file_content):
        """Parse Excel file and map columns."""
        try:
            df = pd.read_excel(file_content)
            
            # Normalize headers
            df.columns = [str(c).strip() for c in df.columns]
            
            # Map columns
            valid_data = []
            errors = []
            
            for index, row in df.iterrows():
                mapped_row = {}
                row_errors = []
                
                for col in df.columns:
                    db_col = self.column_mapping.get(col)
                    if db_col:
                        val = row[col]
                        if pd.notna(val):
                            mapped_row[db_col] = val
                            
                # Validation
                if not mapped_row.get("order_number"):
                    row_errors.append("Missing Order Number")
                if not mapped_row.get("product_name"):
                    row_errors.append("Missing Product Name")
                if not mapped_row.get("quantity"):
                    row_errors.append("Missing Quantity")
                else:
                    try:
                        mapped_row["quantity"] = int(mapped_row["quantity"])
                    except:
                        row_errors.append("Invalid Quantity")

                if row_errors:
                    errors.append({"row": index + 2, "errors": ", ".join(row_errors), "data": mapped_row})
                else:
                    valid_data.append(mapped_row)
                    
            return valid_data, errors, df.columns.tolist()
            
        except Exception as e:
            st.error(f"Error parsing file: {e}")
            return [], [], []

    def import_orders(self, orders_data):
        """Bulk insert orders."""
        success_count = 0
        fail_count = 0
        
        for order in orders_data:
            try:
                # Handle dates
                if "shipping_date" in order:
                     try:
                         # Ensure proper format (YYYY-MM-DD), pandas might give Timestamp
                         if isinstance(order["shipping_date"], pd.Timestamp):
                             order["shipping_date"] = order["shipping_date"].strftime('%Y-%m-%d')
                     except:
                         del order["shipping_date"]

                self.db.client.table("orders").insert(order).execute()
                success_count += 1
            except Exception as e:
                # Duplicate Key Error likely
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
