import streamlit as st
import pandas as pd
from modules.orders.services import OrderService
from modules.orders.impex import ImpexService
from core.config import UserRole

def render():
    st.header("📦 Керування замовленнями")
    
    service = OrderService()
    impex = ImpexService()
    
    tab_list, tab_new, tab_import, tab_export = st.tabs(["📋 Список", "➕ Нове замовлення", "📥 Імпорт (Excel)", "📤 Експорт"])
    
    # --- TAB 1: LIST ---
    with tab_list:
        orders = service.get_orders()
        
        if not orders:
            st.info("Замовлень поки немає.")
        else:
            # Display as DataFrame for now
            df = pd.DataFrame(orders)
            
            # Reorder/Rename columns for display
            display_cols = ["order_number", "product_name", "article", "quantity", "contractor", "shipping_date", "created_at"]
            st.dataframe(
                df, 
                column_config={
                    "order_number": "№ Замовлення",
                    "product_name": "Назва виробу",
                    "article": "Артикул",
                    "quantity": "Кількість",
                    "contractor": "Контрагент",
                    "shipping_date": "Дата відвантаження",
                    "created_at": "Створено"
                },
                use_container_width=True,
                hide_index=True
            )
            
    # --- TAB 2: NEW ORDER ---
    with tab_new:
        user_role = st.session_state.role
        if user_role not in [UserRole.ADMIN, UserRole.MANAGER]:
            st.info("🔒 Створення замовлень доступне тільки для менеджерів та адміністраторів.")
        else:
            with st.form("new_order_form"):
                c1, c2 = st.columns(2)
                with c1:
                    order_number = st.text_input("Номер замовлення (Унікальний)*")
                    product_name = st.text_input("Назва виробу*")
                    article = st.text_input("Артикул")
                with c2:
                    quantity = st.number_input("Кількість*", min_value=1, value=1)
                    contractor = st.text_input("Контрагент")
                    shipping_date = st.date_input("Дата відвантаження")
                
                comment = st.text_area("Коментар")
                
                submitted = st.form_submit_button("Створити замовлення")
                
                if submitted:
                    if not order_number or not product_name:
                        st.error("Будь ласка, заповніть обов'язкові поля.")
                    else:
                        data = {
                            "order_number": order_number,
                            "product_name": product_name,
                            "article": article,
                            "quantity": quantity,
                            "contractor": contractor,
                            "shipping_date": shipping_date.isoformat(),
                            "comment": comment
                        }
                        res = service.create_order(data)
                        if res:
                            st.success(f"Замовлення {order_number} створено! Етапи виробництва згенеровано автоматично.")
    
    # --- TAB 3: IMPORT ---
    with tab_import:
        st.subheader("Масове завантаження замовлень")
        if st.session_state.role not in [UserRole.ADMIN, UserRole.MANAGER]:
             st.info("🔒 Імпорт доступний тільки для менеджерів та адміністраторів.")
        else:
            uploaded_file = st.file_uploader("Оберіть файл Excel (.xlsx)", type=['xlsx'])
            
            if uploaded_file:
                valid_data, errors, headers = impex.parse_excel(uploaded_file)
                
                st.info(f"Знайдено стовпців: {headers}")
                
                c1, c2 = st.columns(2)
                c1.success(f"✅ Коректних рядків: {len(valid_data)}")
                c2.error(f"❌ Помилкових рядків: {len(errors)}")
                
                if errors:
                    with st.expander("Переглянути помилки"):
                        st.write(errors)
                
                if valid_data:
                    st.write("Попередній перегляд (перші 5):")
                    st.dataframe(pd.DataFrame(valid_data).head())
                    
                    if st.button("🚀 Імпортувати в базу"):
                        with st.spinner("Імпорт..."):
                            s, f = impex.import_orders(valid_data)
                        st.success(f"Імпорт завершено! Успішно: {s}, Дублікатів/Помилок: {f}")
                        st.cache_data.clear()

    # --- TAB 4: EXPORT ---
    with tab_export:
        st.subheader("Вивантаження даних")
        if st.button("🔄 Згенерувати файл експорту"):
            excel_data = impex.export_orders()
            if excel_data:
                st.download_button(
                    label="📥 Завантажити Excel",
                    data=excel_data,
                    file_name="orders_export.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            else:
                st.warning("Немає даних для експорту.")
