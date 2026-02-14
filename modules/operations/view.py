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
    # Determine User Role
    is_admin = st.session_state.role == UserRole.ADMIN
    
    # --- TAB 1: LIST & EDIT ---
    with tab_list:
        # 1. Controls Row
        c_search, c_sort, c_limit = st.columns([2, 1, 1])
        
        search_query = c_search.text_input("🔍 Пошук", placeholder="Введіть артикул, ключ або назву...", label_visibility="collapsed")
        
        sort_options = {
            "created_at_desc": "📅 Створено (найновіші)",
            "created_at_asc": "📅 Створено (найстаріші)",
            "updated_at_desc": "📝 Оновлено (найновіші)",
            "article_asc": "🔤 Артикул (А-Я)",
            "article_desc": "🔤 Артикул (Я-А)",
            "section_asc": "🏭 Дільниця (А-Я)",
            "norm_desc": "⏱️ Норма часу (найбільша)"
        }
        sort_by = c_sort.selectbox("Сортування", options=list(sort_options.keys()), format_func=lambda x: sort_options[x], label_visibility="collapsed")
        
        page_size = c_limit.selectbox("Рядків на сторінці", options=[20, 50, 100, 200, 500], index=0, label_visibility="collapsed")

        # 2. Fetch Data
        df = service.get_operations()
        
        if not df.empty:
            # 3. Process Data (Search & Sort) using Pandas
            # Filter
            if search_query:
                query = search_query.lower()
                mask = (
                    df['operation_key'].astype(str).str.lower().str.contains(query) |
                    df['article'].astype(str).str.lower().str.contains(query) |
                    df['operation_number'].astype(str).str.lower().str.contains(query) |
                    df['section'].astype(str).str.lower().str.contains(query)
                )
                df = df[mask]

            # Sort
            if sort_by == 'created_at_desc':
                df = df.sort_values(by='created_at', ascending=False)
            elif sort_by == 'created_at_asc':
                df = df.sort_values(by='created_at', ascending=True)
            elif sort_by == 'updated_at_desc':
                df = df.sort_values(by='updated_at', ascending=False)
            elif sort_by == 'article_asc':
                df = df.sort_values(by='article', ascending=True)
            elif sort_by == 'article_desc':
                df = df.sort_values(by='article', ascending=False)
            elif sort_by == 'section_asc':
                df = df.sort_values(by='section', ascending=True)
            elif sort_by == 'norm_desc':
                df = df.sort_values(by='norm_time', ascending=False)
                
            # 4. Add "No." Column (Sequential 1..N)
            df.insert(0, 'No.', range(1, len(df) + 1))
            
            # 5. Format User Columns
            # Helper to format user
            def format_user(row, prefix):
                email = row.get(f"{prefix}_email")
                name = row.get(f"{prefix}_name")
                if pd.notna(name) and pd.notna(email):
                    return f"{name} ({email})"
                elif pd.notna(email):
                    return email
                return "-"
            
            if 'created_by_email' in df.columns:
                df['created_by_fmt'] = df.apply(lambda x: format_user(x, 'created_by'), axis=1)
            
            if 'updated_by_email' in df.columns:
                df['updated_by_fmt'] = df.apply(lambda x: format_user(x, 'updated_by'), axis=1)
                
            # 6. Pagination
            total_rows = len(df)
            total_pages = (total_rows // page_size) + (1 if total_rows % page_size > 0 else 0)
            
            # Session state for current page
            if "ops_page" not in st.session_state:
                st.session_state.ops_page = 1
                
            # Validate page range (if filter changed)
            if st.session_state.ops_page > total_pages:
                 st.session_state.ops_page = max(1, total_pages)
                 
            current_page = st.session_state.ops_page
            start_idx = (current_page - 1) * page_size
            end_idx = start_idx + page_size
            
            df_page = df.iloc[start_idx:end_idx].copy()
            
            # 7. Display Table
            if is_admin:
                st.info("💡 Режим Адміністратора: Ви можете редагувати таблицю. Не забудьте підтвердити та зберегти зміни.")
            else:
                st.warning("🔒 Режим перегляду: У вас немає прав для редагування.")
            
            # Determine fixed height: (rows * 35px) + header (~40px)
            # Max height constraint
            calc_height = (len(df_page) * 35) + 40
            
            edited_df = st.data_editor(
                df_page,
                key="ops_editor",
                height=calc_height, 
                column_config={
                    "id": None, # Hide ID
                    "No.": st.column_config.NumberColumn("№", width="small", disabled=True),
                    "operation_key": "Ключ",
                    "article": "Артикул",
                    "operation_number": "№ Оп.",
                    "section": "Дільниця",
                    "norm_time": st.column_config.NumberColumn("Норма (хв)", format="%.2f"),
                    "comment": "Коментар",
                    "color": "Колір",
                    # Metadata (Disabled)
                    "created_at": st.column_config.DatetimeColumn("Створено", format="YYYY-MM-DD HH:mm:ss", disabled=True),
                    "updated_at": st.column_config.DatetimeColumn("Оновлено", format="YYYY-MM-DD HH:mm:ss", disabled=True),
                    "created_by_fmt": st.column_config.TextColumn("Створив", disabled=True),
                    "updated_by_fmt": st.column_config.TextColumn("Оновив", disabled=True),
                    
                    # Hide raw columns
                    "created_by": None, "updated_by": None,
                    "created_by_email": None, "created_by_name": None,
                    "updated_by_email": None, "updated_by_name": None
                },
                hide_index=True,
                use_container_width=True,
                disabled=not is_admin, # CRITICAL: Disable for non-admins
                # Force columns order
                column_order=["No.", "operation_key", "article", "operation_number", "section", "norm_time", "color", "comment", "created_by_fmt", "created_at", "updated_by_fmt", "updated_at"]
            )
            
            # 8. Pagination Controls
            c_prev, c_info, c_next = st.columns([1, 2, 1])
            
            with c_prev:
                if current_page > 1:
                    if st.button("⬅️ Попередня"):
                        st.session_state.ops_page -= 1
                        st.rerun()
                        
            with c_info:
                st.markdown(f"<div style='text-align: center'>Сторінка <b>{current_page}</b> з <b>{total_pages}</b> (Всього: {total_rows})</div>", unsafe_allow_html=True)
                
            with c_next:
                if current_page < total_pages:
                    if st.button("Наступна ➡️"):
                        st.session_state.ops_page += 1
                        st.rerun()

            # 9. Save Changes Logic (Admin Only)
            if is_admin:
                st.divider()
                st.markdown("##### 💾 Збереження змін")
                
                # Checkbox confirmation
                confirm_save = st.checkbox("Я підтверджую правильність змін", key="confirm_ops_save")
                
                if st.button("Зберегти зміни в таблиці", type="primary", disabled=not confirm_save):
                    with st.spinner("Збереження..."):
                        updated_count = 0
                        current_user_id = st.session_state.user.id if st.session_state.get("user") else None
                        
                        for index, row in edited_df.iterrows():
                            op_id = row.get("id")
                            
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
                                continue 
                            else:
                                service.update_operation(op_id, row_data, user_id=current_user_id)
                                updated_count += 1
                                
                        st.success(f"✅ Оновлено {updated_count} записів!")
                        st.rerun()
                
                # 10. Delete All (Admin Only, Double Confirm)
                st.divider()
                with st.expander("🗑️ Небезпечна зона (Видалити все)"):
                    st.error("Увага! Ця дія видалить ВСІ операції з бази даних. Це незворотньо.")
                    
                    # Double confirmation pattern
                    confirm_delete_1 = st.checkbox("Я розумію, що дані будуть втрачені назавжди", key="del_all_1")
                    
                    if st.button("🗑️ Видалити ВСІ операції", type="primary", disabled=not confirm_delete_1):
                        # Use a second, explicit confirmation via a temporary container or just require the checkbox logic above.
                        # User asked for "receive confirmation twice". 
                        # Checkbox is one, checking button is action. 
                        # Let's add a second checkbox for "Double Confirmation".
                        st.session_state.show_final_delete_confirm = True
                        
                    if st.session_state.get("show_final_delete_confirm"):
                        st.warning("Ви точно впевнені? Підтвердіть ще раз.")
                        if st.button("💀 ТАК, ВИДАЛИТИ ВСЕ", type="secondary"):
                             if service.delete_all_operations():
                                 st.success("Всі операції успішно видалено.")
                                 st.session_state.show_final_delete_confirm = False
                                 st.rerun()
                             else:
                                 st.error("Помилка при видаленні.")

        else:
            st.info("Довідник порожній. Додайте операції через імпорт або вкладку 'Нова операція'.")

    # --- TAB 2: NEW OPERATION ---
    with tab_new:
        if not is_admin:
             st.warning("⛔ Створення нових операцій доступно тільки адміністраторам.")
        else:
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
                    # Add confirmation check logic within form? 
                    # User said "any changes need to be confirmed". 
                    # Forms have a submit button. It acts as confirmation.
                    # But if we want explicit extra checkbox:
                    pass 
                
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
                        current_user_id = st.session_state.user.id if st.session_state.get("user") else None
                        success, msg = service.create_operation(data, user_id=current_user_id)
                        if success:
                            st.success("Операцію додано!")
                            st.rerun()
                        else:
                            st.error(f"Помилка: {msg}")

    # --- TAB 3: IMPORT ---
    with tab_import:
        if not is_admin:
             st.warning("⛔ Імпорт доступний тільки для Адміністраторів.")
        else:
            st.markdown("### Імпорт операцій з Excel")
            uploaded_file = st.file_uploader("Завантажте файл", type=["xlsx", "xls"])
            
            if uploaded_file:
                try:
                    # 1. Inspect Excel File for Sheets
                    xls = pd.ExcelFile(uploaded_file)
                    sheet_names = xls.sheet_names
                    
                    st.write(f"Знайдено аркушів: {len(sheet_names)}")
                    selected_sheet = st.selectbox("Оберіть аркуш для імпорту", sheet_names)
                    
                    # 2. Read Data from Selected Sheet
                    df_raw = pd.read_excel(uploaded_file, sheet_name=selected_sheet)
                    
                    st.success(f"Файл завантажено! Рядків: {len(df_raw)}")
                    st.write("Попередній перегляд (перші 3 рядки):")
                    # Convert to string for display to avoid Arrow serialization errors with mixed types (e.g. int/str in same col)
                    st.dataframe(df_raw.head(3).astype(str))
                    
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
                    
                    st.divider()
                    
                    if not mapping:
                        st.warning("⚠️ Спочатку співставте хоча б один стовпець.")
                    else:
                        # --- PRE-IMPORT VALIDATION ---
                        # 1. Identify mapped columns in the dataframe
                        mapped_excel_cols = [v for k, v in mapping.items() if v]
                        
                        # 2. Analyze rows
                        df_mapped_subset = df_raw[mapped_excel_cols]
                        total_rows = len(df_mapped_subset)
                        
                        # Empty check
                        is_empty_mask = df_mapped_subset.replace(r'^\s*$', pd.NA, regex=True).isna().all(axis=1)
                        empty_rows_count = is_empty_mask.sum()
                        valid_rows_count = total_rows - empty_rows_count
                        
                        # 3. DUPLICATE CHECK
                        # We need to know which column maps to 'operation_key'
                        key_col_name = mapping.get("operation_key")
                        duplicate_count = 0
                        new_count = 0
                        
                        if key_col_name and key_col_name != "(Пропустити)":
                            # Fetch existing keys
                            existing_keys = service.get_all_keys()
                            
                            # Get keys from import (clean them)
                            import_keys = df_raw[key_col_name].dropna().astype(str).tolist()
                            
                            # Count overlap
                            # Note: This doesn't account for skipping empty rows yet, but gives a rough idea.
                            # Better: Check only on valid rows
                            
                            # Let's iterate valid rows to be precise
                            # Improve: Vectorized check
                            valid_df = df_raw[~is_empty_mask].copy()
                            if key_col_name in valid_df.columns:
                                valid_df['is_duplicate'] = valid_df[key_col_name].astype(str).isin(existing_keys)
                                duplicate_count = valid_df['is_duplicate'].sum()
                                new_count = len(valid_df) - duplicate_count
                            else:
                                new_count = len(valid_df)
                                
                        else:
                            st.warning("⚠️ Не вибрано стовпець 'Ключ операції'. Перевірка дублікатів неможлива.")
                            new_count = valid_rows_count

                        # Display Stats
                        st.markdown("#### 📊 Аналіз даних")
                        c_stat1, c_stat2, c_stat3, c_stat4 = st.columns(4)
                        c_stat1.metric("Всього рядків", total_rows)
                        c_stat2.metric("Пусті", empty_rows_count)
                        c_stat3.metric("Нові", new_count, delta_color="normal")
                        c_stat4.metric("Існуючі (Дублі)", duplicate_count, delta_color="inverse")
                        
                        # Options
                        st.divider()
                        c_opt1, c_opt2 = st.columns(2)
                        
                        skip_empty = c_opt1.checkbox("🚫 Не імпортувати пусті рядки", value=True)
                        
                        import_mode = c_opt2.radio(
                            "Дії з дублікатами:",
                            ["Пропустити", "Оновити (Перезаписати)"],
                            index=0,
                            help="Пропустити: старі дані залишаться. Оновити: дані з файлу замінять старі."
                        )
                        update_existing = (import_mode == "Оновити (Перезаписати)")
                        
                        confirm_import = st.checkbox("✅ Підтверджую імпорт даних (це змінить базу)", key="conf_imp")

                        if valid_rows_count == 0:
                            st.error("❌ Немає даних для імпорту (всі рядки пусті або не вибрані стовпці).")
                        else:
                            if st.button("🚀 Виконати імпорт", disabled=not confirm_import):
                                with st.spinner("Імпортуємо дані..."):
                                    # Filter DF if needed
                                    if skip_empty:
                                        # Keep only rows that are NOT empty
                                        df_to_import = df_raw[~is_empty_mask]
                                    else:
                                        df_to_import = df_raw
                                        
                                    current_user_id = st.session_state.user.id if st.session_state.get("user") else None
                                    
                                    s_count, e_count = service.import_operations(
                                        df_to_import, 
                                        mapping, 
                                        user_id=current_user_id,
                                        update_existing=update_existing
                                    )
                                
                                if e_count == 0:
                                    st.success(f"✅ Успішно оброблено {s_count} рядків!")
                                    st.balloons()
                                else:
                                    st.warning(f"Імпорт завершено. Успішно: {s_count}, Помилок: {e_count}")
                                    
                except Exception as e:
                    st.error(f"Помилка читання або обробки файлу: {e}")

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
