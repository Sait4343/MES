import streamlit as st
import pandas as pd
from modules.operations.services import OperationsService
from core.config import UserRole

def render():
    st.header("🧵 Довідник Операцій")
    
    service = OperationsService()
    
    tab_list, tab_import = st.tabs(["📋 Список", "📥 Імпорт (Excel)"])
    
    # --- TAB 1: LIST ---
    with tab_list:
        df = service.get_operations()
        if not df.empty:
            # We can use data_editor for inline edits later potentially
            st.dataframe(
                df, 
                column_config={
                    "operation_key": "Ключ",
                    "article": "Артикул",
                    "operation_number": "№ Оп.",
                    "section": "Дільниця",
                    "norm_time": st.column_config.NumberColumn("Норма (хв)", format="%.2f"),
                    "comment": "Коментар",
                    "color": "Колір",
                    "created_at": st.column_config.DatetimeColumn("Створено", format="DD.MM.YYYY HH:mm")
                },
                hide_index=True,
                use_container_width=True
            )
        else:
            st.info("Довідник порожній.")

    # --- TAB 2: IMPORT ---
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
