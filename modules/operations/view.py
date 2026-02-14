import streamlit as st
import pandas as pd
from modules.operations.services import OperationsService
from core.config import UserRole

def render():
    st.header("🧵 Довідник Операцій")
    
    service = OperationsService()
    
    # Create tabs
    tab_list, tab_new, tab_import, tab_export = st.tabs(["📋 Список і Редагування", "➕ Нова операція", "📥 Імпорт (Excel)", "📤 Експорт"])
    
    # --- TAB 1: LIST & EDIT ---
    with tab_list:
        df = service.get_operations()
        if not df.empty:
            st.info("💡 Ви можете редагувати дані прямо в таблиці. Натисніть Enter або клікніть за межами клітинки для збереження змін.")
            
            # Use data_editor
            edited_df = st.data_editor(
                df,
                key="ops_editor",
                column_config={
                    "id": None, # Hide ID
                    "operation_key": "Ключ",
                    "article": "Артикул",
                    "operation_number": "№ Оп.",
                    "section": "Дільниця",
                    "norm_time": st.column_config.NumberColumn("Норма (хв)", format="%.2f"),
                    "comment": "Коментар",
                    "color": "Колір",
                    "created_at": st.column_config.DatetimeColumn("Створено", format="DD.MM.YYYY HH:mm", disabled=True)
                },
                hide_index=True,
                use_container_width=True,
                num_rows="dynamic" # Allow adding/deleting rows if supported by backend logic logic below
            )

            # Detect changes (This is a simplified "snapshot" approach. 
            # Real-time sync requires comparing edited_df with df, or using on_change callback)
            # For simplicity in this interaction model, we can add a "Save Changes" button 
            # OR process changes immediately if identifying what changed is easy.
            # Ideally, data_editor returns the new state. We need to find Diff.
            
            # Simple Diff Logic for Updates:
            if not df.equals(edited_df):
                # We need to identify what changed.
                # However, st.data_editor state persistence can be tricky without a button or callback.
                # Let's try to capture changes via session state if needed, 
                # but standard practice: Button to commit bulk edits OR iterative updates.
                
                # Iterating rows to find changes:
                # This is heavy if DF is large.
                # Constraint: We only want to save specific changes.
                
                if st.button("💾 Зберегти зміни в таблиці"):
                    with st.spinner("Збереження..."):
                        # Identify revised rows
                        # Assuming 'id' is prevalent.
                        
                        # 1. Updates
                        for index, row in edited_df.iterrows():
                            # Find original row by ID
                            # This is O(N^2) effectively if not optimized, but OK for small catalogs.
                            # Better: compare based on ID index.
                             
                            # If new row (no ID or ID is NaN if added via dynamic), Handle Create
                            # Note: Supabase/Pandas handling of new rows in data_editor usually results in empty IDs.
                            
                            op_id = row.get("id")
                            
                            # Clean data for DB
                            row_data = {
                                "operation_key": row["operation_key"],
                                "article": row["article"],
                                "operation_number": row["operation_number"],
                                "section": row["section"],
                                "norm_time": row["norm_time"],
                                "comment": row["comment"],
                                "color": row["color"]
                            }
                            
                            if pd.isna(op_id):
                                # It's a NEW row added via UI
                                service.create_operation(row_data)
                            else:
                                # It's an UPDATE. Check if changed? 
                                # For simplicity, just update all (or filter).
                                # To avoid spamming DB, we should compare.
                                pass
                                # We'll rely on "New Operation" tab for adding mainly, 
                                # and use this mainly for edits.
                                # But let's support updates.
                                service.update_operation(op_id, row_data)
                                
                        # 2. Deletes
                        # st.data_editor allows deleting rows. We need to find IDs that are in DB but not in edited_df.
                        original_ids = df["id"].tolist()
                        current_ids = [x for x in edited_df["id"].tolist() if pd.notna(x)]
                        
                        ids_to_delete = set(original_ids) - set(current_ids)
                        for d_id in ids_to_delete:
                            service.delete_operation(d_id)
                            
                        st.success("Зміни збережено!")
                        st.rerun()

        else:
            st.info("Довідник порожній. Додайте операції через імпорт або вкладку 'Нова операція'.")

    # --- TAB 2: NEW OPERATION ---
    with tab_new:
        st.subheader("➕ Додати нову операцію")
        with st.form("new_op_form"):
            c1, c2 = st.columns(2)
            op_key = c1.text_input("Ключ операції (Operation Key)", help="Унікальний ідентифікатор")
            article = c2.text_input("Артикул")
            
            c3, c4 = st.columns(2)
            op_num = c3.text_input("Номер операції")
            section = c4.text_input("Дільниця (Section)")
            
            c5, c6 = st.columns(2)
            norm_time = c5.number_input("Норма часу (хв)", min_value=0.0, step=0.01)
            color = c6.color_picker("Колір", "#E0E0E0")
            
            comment = st.text_area("Коментар")
            
            if st.form_submit_button("Створити операцію"):
                if not op_key or not article:
                    st.error("Ключ та Артикул є обов'язковими!")
                else:
                    data = {
                        "operation_key": op_key,
                        "article": article,
                        "operation_number": op_num,
                        "section": section,
                        "norm_time": norm_time,
                        "comment": comment,
                        "color": color
                    }
                    success, msg = service.create_operation(data)
                    if success:
                        st.success("Операцію додано!")
                        st.rerun()
                    else:
                        st.error(f"Помилка: {msg}")

    # --- TAB 3: IMPORT ---
    with tab_import:
        if st.session_state.role not in [UserRole.ADMIN, UserRole.MANAGER]:
            st.warning("⚠️ Імпорт доступний тільки для Адміністраторів та Менеджерів.")
        else:
            st.markdown("### Імпорт операцій з Excel")
            uploaded_file = st.file_uploader("Завантажте файл", type=["xlsx", "xls"])
            
            if uploaded_file:
                try:
                    df_raw = pd.read_excel(uploaded_file)
                    st.success(f"Файл завантажено! Рядків: {len(df_raw)}")
                    st.write("Попередній перегляд (перші 3 рядки):")
                    st.dataframe(df_raw.head(3))
                    
                    st.divider()
                    st.subheader("🔗 Налаштування стовпців")
                    st.info("Оберіть, який стовпець з вашого файлу відповідає полю в базі даних.")
                    
                    excel_headers = ["(Пропустити)"] + list(df_raw.columns)
                    
                    # DB Fields we need to map
                    db_fields = {
                        "operation_key": "Ключ операції",
                        "article": "Артикул",
                        "operation_number": "№ операції",
                        "section": "Дільниця",
                        "norm_time": "Норма часу (хв)",
                        "comment": "Коментар",
                        "color": "Колір" # Optional but good to have
                    }
                    
                    mapping = {}
                    cols = st.columns(3)
                    
                    for i, (db_field, label) in enumerate(db_fields.items()):
                        # Try to auto-guess index
                        default_idx = 0
                        for idx, h in enumerate(excel_headers):
                            if h != "(Пропустити)" and any(x in h.lower() for x in label.lower().split()):
                                default_idx = idx
                                break
                        
                        with cols[i % 3]:
                            selected_col = st.selectbox(
                                f"Поле БД: **{label}**", 
                                options=excel_headers, 
                                index=default_idx,
                                key=f"map_{db_field}"
                            )
                            if selected_col != "(Пропустити)":
                                mapping[db_field] = selected_col
                    
                    st.divider()
                    
                    if st.button("🚀 Виконати імпорт"):
                        if not mapping:
                            st.error("Ви не співставили жодного стовпця!")
                        else:
                            with st.spinner("Імпортуємо дані..."):
                                s_count, e_count = service.import_operations(df_raw, mapping)
                            
                            if e_count == 0:
                                st.success(f"✅ Успішно імпортовано {s_count} рядків!")
                                st.balloons()
                            else:
                                st.warning(f"Імпорт завершено. Успішно: {s_count}, Помилок: {e_count}")
                                
                except Exception as e:
                    st.error(f"Помилка читання файлу: {e}")

    # --- TAB 3: EXPORT ---
    with tab_export:
        st.markdown("### Експорт операцій в Excel")
        
        # Re-fetch or reuse if appropriate, but cleaner to fetch fresh
        df_export = service.get_operations()
        
        if df_export.empty:
            st.info("Немає даних для експорту.")
        else:
            st.write(f"У базі знайдено {len(df_export)} записів.")
            
            # Convert to Excel in memory
            import io
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df_export.to_excel(writer, index=False, sheet_name='Operations')
            
            excel_data = output.getvalue()
            
            st.download_button(
                label="📥 Завантажити Excel",
                data=excel_data,
                file_name="operations_catalog.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
