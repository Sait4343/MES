import streamlit as st
import pandas as pd
from modules.sections.services import SectionsService
from core.config import UserRole

def render():
    st.header("🏭 Дільниці (Sections)")
    
    service = SectionsService()
    sections_df = service.get_all_sections()
    source_op_types = service.get_operation_types_source()
    
    tab_list, tab_new, tab_import, tab_export = st.tabs(["📋 Список і Редагування", "➕ Нова дільниця", "📥 Імпорт", "📤 Експорт"])
    
    # --- TAB 1: LIST & EDIT ---
    with tab_list:
        if sections_df.empty:
            st.info("Дільниць ще немає.")
        else:
            st.info("💡 Редагуйте назву та потужність в таблиці. Для зміни типів операцій використовуйте детальну форму нижче.")
            
            # Helper: Convert array to string for display in editor if needed, 
            # but st.column_config.ListColumn works for display.
            
            edited_df = st.data_editor(
                sections_df,
                key="sections_editor",
                column_config={
                    "id": None,
                    "name": "Назва дільниці",
                    "description": "Опис",
                    "capacity_minutes": st.column_config.NumberColumn("Потужність (хв)", help="Час, який можна задіяти на дільниці"),
                    "operation_types": st.column_config.ListColumn("Типи операцій"),
                    "created_at": None,
                    "updated_at": None
                },
                hide_index=True,
                use_container_width=True
            )
            
            if st.button("💾 Зберегти зміни таблиці"):
                for index, row in edited_df.iterrows():
                    s_id = row['id']
                    # We only update scalar fields here to be safe
                    update_data = {
                        "name": row['name'],
                        "description": row['description'],
                        "capacity_minutes": row['capacity_minutes']
                    }
                    service.update_section(s_id, update_data)
                st.success("Зміни збережено!")
                st.rerun()
                
            st.divider()
            st.subheader("🛠️ Налаштування типів операцій")
            
            # Select Section
            sec_options = {r['id']: r['name'] for r in sections_df.to_dict('records')}
            selected_sec_id = st.selectbox("Оберіть дільницю", list(sec_options.keys()), format_func=lambda x: sec_options[x])
            
            if selected_sec_id:
                # Get current data
                curr_sec = sections_df[sections_df['id'] == selected_sec_id].iloc[0]
                curr_ops = curr_sec.get('operation_types') or []
                
                with st.form("sec_ops_form"):
                    st.write(f"**Дільниця:** {curr_sec['name']}")
                    new_ops = st.multiselect(
                        "Типи операцій (із довідника операцій)",
                        options=source_op_types,
                        default=[x for x in curr_ops if x in source_op_types]
                    )
                    
                    if st.form_submit_button("Зберегти типи"):
                        service.update_section(selected_sec_id, {"operation_types": new_ops})
                        st.success("Типи операцій оновлено!")
                        st.rerun()

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
                    success, msg = service.create_section(data)
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
                    s, e = service.import_sections(df_raw, cols_map)
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
