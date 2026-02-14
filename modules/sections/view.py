import streamlit as st
import pandas as pd
from modules.sections.services import SectionsService
from core.config import UserRole
from zoneinfo import ZoneInfo

# --- HELPER FUNCTIONS ---
def get_kyiv_time(dt_str):
    if not dt_str:
        return ""
    try:
        dt = pd.to_datetime(dt_str)
        if dt.tz is None:
            dt = dt.tz_localize("UTC")
        return dt.tz_convert(ZoneInfo("Europe/Kyiv")).strftime("%d.%m.%Y %H:%M")
    except:
        return str(dt_str)

@st.dialog("📋 Операції дільниці")
def view_section_operations(section_name):
    st.caption(f"Список операцій для дільниці: **{section_name}**")
    
    service = SectionsService()
    ops_df = service.get_operations_by_section(section_name)
    
    if ops_df.empty:
        st.warning("Для цієї дільниці не знайдено операцій в каталозі.")
    else:
        # Simple grid for operations
        st.dataframe(
            ops_df,
            column_config={
                "operation_number": "№ Оп",
                "article": "Артикул",
                "norm_time": st.column_config.NumberColumn("Норма (хв)", format="%.2f"),
                "comment": "Коментар",
                "created_at": None,
                "updated_at": None,
                "created_by": None,
                "updated_by": None,
                "id": None,
                "operation_key": None
            },
            hide_index=True,
            use_container_width=True,
            height=400
        )
        st.info(f"Всього операцій: {len(ops_df)}")

def render():
    st.header("🏭 Дільниці (Sections)")
    
    service = SectionsService()
    sections_df = service.get_all_sections()
    source_op_types = service.get_operation_types_source()
    
    tab_list, tab_new, tab_import, tab_export = st.tabs(["📋 Список і Редагування", "➕ Нова дільниця", "📥 Імпорт", "📤 Експорт"])
    
    # --- TAB 1: LIST & EDIT ---
    with tab_list:
        # Controls
        c_search, c_limit = st.columns([3, 1])
        search_query = c_search.text_input("🔍 Пошук", placeholder="Назва або опис...", label_visibility="collapsed")
        limit = c_limit.selectbox("Рядків", [20, 50, 100, 200], index=0, label_visibility="collapsed")
        
        # Filter Logic
        if not sections_df.empty:
            df_display = sections_df.copy()
            
            # Search
            if search_query:
                mask = df_display.astype(str).apply(lambda x: x.str.contains(search_query, case=False, na=False)).any(axis=1)
                df_display = df_display[mask]
            
            # Pagination
            total_items = len(df_display)
            if total_items > limit:
                # Page control
                num_pages = (total_items // limit) + (1 if total_items % limit > 0 else 0)
                page = st.number_input(f"Сторінка (із {num_pages})", min_value=1, max_value=num_pages, value=1)
                start_idx = (page - 1) * limit
                end_idx = start_idx + limit
                df_page = df_display.iloc[start_idx:end_idx].copy()
                start_counter = start_idx + 1
            else:
                df_page = df_display.copy()
                start_counter = 1
            
            # Add "No." column
            df_page.insert(0, "No.", range(start_counter, start_counter + len(df_page)))
            
            # Format User/Date Columns
            for col in ['created_at', 'updated_at']:
                if col in df_page.columns:
                    df_page[col] = df_page[col].apply(get_kyiv_time)
            
            # Formatting "Created By"
            if 'created_by_name' in df_page.columns:
                df_page['Створено'] = df_page['created_by_name'].fillna("-") + "\n" + df_page['created_at'].fillna("")
            if 'updated_by_name' in df_page.columns:
                df_page['Оновлено'] = df_page['updated_by_name'].fillna("-") + "\n" + df_page['updated_at'].fillna("")

            # Fixed Height Calculation
            row_height = 35
            header_height = 40
            table_height = (len(df_page) * row_height) + header_height + 10
            
            st.caption(f"Відображено {len(df_page)} із {total_items} дільниць")
            
            # EDITABLE GRID
            edited_df = st.data_editor(
                df_page,
                key="sections_editor",
                column_config={
                    "id": None,
                    "No.": st.column_config.NumberColumn("№", width="small", disabled=True),
                    "name": st.column_config.TextColumn("Назва дільниці", width="medium"),
                    "description": st.column_config.TextColumn("Опис", width="large"),
                    "capacity_minutes": st.column_config.NumberColumn("Потужність (хв)", help="Час, який можна задіяти на дільниці"),
                    "operation_types": st.column_config.ListColumn("Типи операцій"),
                    "created_at": None, "updated_at": None,
                    "created_by": None, "updated_by": None,
                    "created_by_name": None, "updated_by_name": None,
                    "Створено": st.column_config.TextColumn("Створив", disabled=True, width="medium"),
                    "Оновлено": st.column_config.TextColumn("Оновив", disabled=True, width="medium")
                },
                hide_index=True,
                use_container_width=True,
                height=table_height
            )
            
            # --- ACTION BAR ---
            c_save, c_ops = st.columns([1, 2])
            
            # Save Logic
            if c_save.button("💾 Зберегти зміни", type="primary"):
                current_user_id = st.session_state.user.id if st.session_state.get("user") else None
                changes_count = 0
                
                # Check for changes
                # Note: df_page is source, edited_df is result. 
                # Ideally we compare, but simple iteration is acceptable for small pages.
                
                for index, row in edited_df.iterrows():
                    # We need to find the original ID. 'id' is in the dataframe because we passed it
                    s_id = row.get('id')
                    original_row = sections_df[sections_df['id'] == s_id].iloc[0] if s_id in sections_df['id'].values else None
                    
                    if original_row is not None:
                        # Detect diff
                        diff = {}
                        if row['name'] != original_row['name']: diff['name'] = row['name']
                        if row['description'] != original_row['description']: diff['description'] = row['description']
                        if row['capacity_minutes'] != original_row['capacity_minutes']: diff['capacity_minutes'] = row['capacity_minutes']
                        
                        if diff:
                            service.update_section(s_id, diff, user_id=current_user_id)
                            changes_count += 1
                
                if changes_count > 0:
                    st.success(f"Оновлено {changes_count} записів!")
                    st.rerun()
                else:
                    st.info("Змін не виявлено.")

            # View Operations Logic
            # We need a selector because we can't click rows in data_editor to trigger an action easily without selection_mode,
            # but data_editor doesn't support generic row selection nicely with editing.
            # So we use a selectbox "Select Section to View Operations" populated from the current page.
            
            with c_ops:
                 # Helper to pick a section
                 sec_map = {row['name']: row['name'] for _, row in df_page.iterrows()}
                 selected_section_name = st.selectbox(
                     "Переглянути операції для дільниці:", 
                     [""] + list(sec_map.keys()),
                     format_func=lambda x: "Виберіть..." if x == "" else x,
                     label_visibility="collapsed"
                 )
                 
                 if selected_section_name:
                     view_section_operations(selected_section_name)

        else:
            st.info("Дільниць ще немає.")

    # --- TAB 2: NEW SECTION ---
    with tab_new:
        st.subheader("Створити нову дільницю")
        with st.form("new_sec_form"):
            name = st.text_input("Назва дільниці")
            desc = st.text_area("Опис")
            cap = st.number_input("Потужність (хв)", min_value=0)
            
            ops = st.multiselect("Типи операцій", options=source_op_types)
            
            if st.form_submit_button("Створити"):
                if not name:
                    st.error("Назва обов'язкова!")
                else:
                    data = {
                        "name": name, 
                        "description": desc,
                        "capacity_minutes": cap,
                        "operation_types": ops
                    }
                    current_user_id = st.session_state.user.id if st.session_state.get("user") else None
                    success, msg = service.create_section(data, user_id=current_user_id)
                    if success:
                        st.success("Дільницю створено!")
                        st.rerun()
                    else:
                        st.error(f"Помилка: {msg}")

    # --- TAB 3: IMPORT ---
    with tab_import:
        uploaded_file = st.file_uploader("Excel файл", type=["xlsx", "xls"])
        if uploaded_file:
            try:
                xls = pd.ExcelFile(uploaded_file)
                sheet = st.selectbox("Аркуш", xls.sheet_names)
                df_raw = pd.read_excel(uploaded_file, sheet_name=sheet)
                
                st.write(df_raw.head())
                
                st.write("#### Співставлення")
                cols_map = {}
                db_fields = {
                    "name": "Назва",
                    "capacity_minutes": "Потужність (хв)",
                    "description": "Опис",
                    "operation_types": "Типи операцій (через кому)"
                }
                excel_headers = ["(Пропустити)"] + list(df_raw.columns)
                
                c_cols = st.columns(2)
                for i, (k, v) in enumerate(db_fields.items()):
                    with c_cols[i % 2]:
                        cols_map[k] = st.selectbox(v, excel_headers, key=f"s_map_{k}")
                        
                if st.button("🚀 Імпорт"):
                    current_user_id = st.session_state.user.id if st.session_state.get("user") else None
                    s, e = service.import_sections(df_raw, cols_map, user_id=current_user_id)
                    st.success(f"Успішно: {s}, Помилок: {e}")
                    
            except Exception as e:
                st.error(f"Error: {e}")

    # --- TAB 4: EXPORT ---
    with tab_export:
        if st.button("Експорт в Excel"):
            import io
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer) as writer:
                sections_df.to_excel(writer, index=False)
                
            st.download_button("Завантажити", buffer.getvalue(), "sections.xlsx")
