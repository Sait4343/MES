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
            st.info("💡 Ви можете редагувати дані прямо в таблиці. Натисніть 'Зберегти зміни' щоб зафіксувати.")
            
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

            # 9. Save Changes Logic
            # Compare edited_df with df_page (using IDs)
            # Simplified: Button to save all
            
            if st.button("💾 Зберегти зміни в таблиці", type="primary"):
                with st.spinner("Збереження..."):
                    updated_count = 0
                    current_user_id = st.session_state.user.id if st.session_state.get("user") else None
                    
                    for index, row in edited_df.iterrows():
                        op_id = row.get("id")
                        
                        # Prepare data
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
                            continue # Ignore new rows here? or Create? 
                            # Data_editor dynamic rows usually have None ID.
                            # But wait, original DF has IDs.
                            # If row was added via "dynamic" num_rows, it has no ID.
                            # service.create_operation(row_data, user_id=current_user_id)
                        else:
                            # It's an update
                            # Check change? For now, we update if ID exists.
                            # Optimization: only update if changed.
                            service.update_operation(op_id, row_data, user_id=current_user_id)
                            updated_count += 1
                            
                    st.success(f"Оновлено {updated_count} записів!")
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
                    current_user_id = st.session_state.user.id if st.session_state.get("user") else None
                    success, msg = service.create_operation(data, user_id=current_user_id)
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
                        # We consider a row "empty" if ALL mapped columns are empty/NaN
                        # We consider a row "valid" if at least one mapped column has data
                        
                        # Create a subset for analysis
                        df_mapped_subset = df_raw[mapped_excel_cols]
                        
                        # Count total
                        total_rows = len(df_mapped_subset)
                        
                        # Identify empty rows (all null/nan in mapped cols)
                        # We use .isna().all(axis=1) (or check for empty strings too if needed)
                        # Let's treat empty strings as NaN for this check
                        is_empty_mask = df_mapped_subset.replace(r'^\s*$', pd.NA, regex=True).isna().all(axis=1)
                        empty_rows_count = is_empty_mask.sum()
                        valid_rows_count = total_rows - empty_rows_count
                        
                        # Display Stats
                        st.markdown("#### 📊 Аналіз даних")
                        c_stat1, c_stat2, c_stat3 = st.columns(3)
                        c_stat1.metric("Всього рядків", total_rows)
                        c_stat2.metric("Пусті рядки", empty_rows_count, delta_color="inverse")
                        c_stat3.metric("До імпорту", valid_rows_count)
                        
                        # Options
                        skip_empty = st.checkbox("🚫 Не імпортувати пусті рядки", value=True)
                        
                        if valid_rows_count == 0:
                            st.error("❌ Немає даних для імпорту (всі рядки пусті або не вибрані стовпці).")
                        else:
                            if st.button("🚀 Виконати імпорт"):
                                with st.spinner("Імпортуємо дані..."):
                                    # Filter DF if needed
                                    if skip_empty:
                                        # Keep only rows that are NOT empty
                                        df_to_import = df_raw[~is_empty_mask]
                                    else:
                                        df_to_import = df_raw
                                        
                                    current_user_id = st.session_state.user.id if st.session_state.get("user") else None
                                    s_count, e_count = service.import_operations(df_to_import, mapping, user_id=current_user_id)
                                
                                if e_count == 0:
                                    st.success(f"✅ Успішно імпортовано {s_count} рядків!")
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
