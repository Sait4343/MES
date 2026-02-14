import streamlit as st
import pandas as pd
from modules.workers.services import WorkerService
from core.config import UserRole, ROLE_LABELS
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

def render():
    st.header("👥 Керування працівниками")
    
    # Check if current user is Admin
    current_role = st.session_state.role
    is_admin = current_role == UserRole.ADMIN
    
    if not is_admin:
        st.warning("Доступ заборонено. Тільки адміністратори можуть керувати працівниками.")
        return

    service = WorkerService()
    
    # Fetch data
    workers = service.get_all_workers()
    op_types_options = service.get_operation_types() # Unique sections from operations
    
    tab_list, tab_import, tab_export = st.tabs(["👥 Список і Редагування", "📥 Імпорт (Excel)", "📤 Експорт"])

    # --- TAB 1: LIST & EDIT ---
    with tab_list:
        if not workers:
            st.info("Немає користувачів.")
        else:
            # Prepare DataFrame
            df_workers = pd.DataFrame(workers)
            
            # Ensure columns exist
            for col in ['position', 'competence', 'operation_types', 'comment', 'created_by_name']:
                if col not in df_workers.columns:
                    df_workers[col] = None

            # Add "No." column
            df_workers.insert(0, "No.", range(1, len(df_workers) + 1))
            
            # Add "Delete?" column for UI actions (default False)
            df_workers.insert(0, "Delete?", False)
            
            # Format User/Date Columns
            for col in ['created_at', 'updated_at']:
                if col in df_workers.columns:
                    df_workers[col] = df_workers[col].apply(get_kyiv_time)
            
            # Formatting "Created By"
            if 'created_by_name' in df_workers.columns:
                df_workers['Створено'] = df_workers['created_by_name'].fillna("-") + "\n" + df_workers['created_at'].fillna("")

            st.write("### 📝 Швидке редагування")
            st.caption("Редагуйте Посаду, Компетенцію та Коментарі в таблиці. Для зміни Типів операцій використовуйте детальну форму нижче.")
            st.caption("⚠️ Щоб видалити працівників, поставте галочку в колонці 'Видалити?' і натисніть кнопку 'Видалити обраних' внизу.")

            edited_df = st.data_editor(
                df_workers,
                key="workers_editor",
                column_config={
                     "id": None,
                     "email": None, # Hide Email
                     "Delete?": st.column_config.CheckboxColumn("Видалити?", width="small", help="Оберіть для видалення"),
                     "No.": st.column_config.NumberColumn("№", width="small", disabled=True),
                     "full_name": "ПІБ",
                     "role": st.column_config.SelectboxColumn("Роль", options=[UserRole.ADMIN, UserRole.MANAGER, UserRole.WORKER, UserRole.VIEWER]),
                     "position": "Посада",
                     "competence": "Компетенція",
                     "comment": st.column_config.TextColumn("Коментар", width="medium"),
                     "operation_types": st.column_config.ListColumn("Типи операцій (Дільниці)"),
                     "Створено": st.column_config.TextColumn("Додав", disabled=True, width="medium"),
                     "created_at": None, "updated_at": None, "created_by": None, "updated_by": None, "created_by_name": None, "updated_by_name": None
                },
                hide_index=True,
                use_container_width=True,
                height=500
            )
            
            c1, c2 = st.columns([1, 4])
            
            with c1:
                 # Delete Button
                if st.button("🗑️ Видалити обраних", type="primary"):
                    to_delete = edited_df[edited_df['Delete?'] == True]
                    if not to_delete.empty:
                        rows_deleted = 0
                        for index, row in to_delete.iterrows():
                            if service.delete_worker(row['id']):
                                rows_deleted += 1
                        
                        if rows_deleted > 0:
                            st.success(f"Видалено {rows_deleted} працівників.")
                            st.rerun()
                    else:
                        st.info("Не обрано жодного працівника для видалення.")

            with c2:
                # Save Button for Table Edits
                if st.button("💾 Зберегти зміни таблиці"):
                    current_user_id = st.session_state.user.id if st.session_state.get("user") else None
                    changes_count = 0
                    for index, row in edited_df.iterrows():
                        # Check against original (naive check or just update all)
                        # We'll just update fields that are editable in table
                        
                        uid = row['id']
                        update_data = {
                            "full_name": row['full_name'],
                            "role": row['role'],
                            "position": row['position'],
                            "competence": row['competence'],
                            "comment": row['comment']
                        }
                        service.update_worker_profile(uid, update_data, current_user_id)
                        changes_count += 1
                    
                    st.success("Дані оновлено!")
                    st.rerun()

            st.divider()
            st.subheader("🛠️ Детальне налаштування (Типи операцій)")
            
            # Select Worker to Edit
            worker_options = {w['id']: f"{w.get('full_name')}" for w in workers}
            selected_w_id = st.selectbox("Оберіть працівника для налаштування", list(worker_options.keys()), format_func=lambda x: worker_options[x])
            
            if selected_w_id:
                # Find current worker data
                w_data = next((w for w in workers if w['id'] == selected_w_id), None)
                if w_data:
                    with st.form("worker_detail_form"):
                        st.write(f"**Працівник:** {w_data.get('full_name')}")
                        
                        # Multi-select for Operation Types (Sections)
                        current_ops = w_data.get('operation_types') or []
                        
                        selected_ops = st.multiselect(
                            "Типи операцій (доступ до дільниць)", 
                            options=op_types_options,
                            default=[op for op in current_ops if op in op_types_options]
                        )
                        
                        if st.form_submit_button("Зберегти типи операцій"):
                            current_user_id = st.session_state.user.id if st.session_state.get("user") else None
                            service.update_worker_profile(selected_w_id, {"operation_types": selected_ops}, current_user_id)
                            st.success("Типи операцій оновлено!")
                            st.rerun()

    # --- TAB 2: IMPORT ---
    with tab_import:
        st.markdown("### Імпорт/Оновлення працівників")
        st.info("ℹ️ Імпорт оновлює дані існуючих користувачів за **ПІБ (Full Name)**. Нові користувачі не створюються автоматично.")
        
        uploaded_file = st.file_uploader("Завантажте файл", type=["xlsx", "xls"])
        
        if uploaded_file:
            try:
                xls = pd.ExcelFile(uploaded_file)
                sheet_names = xls.sheet_names
                selected_sheet = st.selectbox("Оберіть аркуш", sheet_names)
                
                df_raw = pd.read_excel(uploaded_file, sheet_name=selected_sheet)
                st.write(df_raw.head())
                
                st.divider()
                st.write("#### Співставлення стовпців")
                
                db_fields_single = {
                    "full_name": "ПІБ (Обов'язково)",
                    "position": "Посада",
                    "competence": "Компетенція",
                    "comment": "Коментар"
                }
                
                excel_headers = ["(Пропустити)"] + list(df_raw.columns)
                excel_headers_clean = list(df_raw.columns) # For multiselect
                
                mapping = {}
                cols = st.columns(2)
                
                # Single Value Mappings
                for i, (k, v) in enumerate(db_fields_single.items()):
                    with cols[i % 2]:
                        mapping[k] = st.selectbox(f"{v}", excel_headers, key=f"w_map_{k}")

                # Multi Value Mapping
                st.write("Merge Columns for Operation Types:")
                mapping["operation_types"] = st.multiselect(
                    "Типи операцій (Оберіть декілька стовпців)", 
                    options=excel_headers_clean
                )
                
                if st.button("🚀 Імпортувати"):
                    with st.spinner("Обробка..."):
                        current_user_id = st.session_state.user.id if st.session_state.get("user") else None
                        s, e = service.import_workers(df_raw, mapping, user_id=current_user_id)
                    if s > 0:
                        st.success(f"Оновлено {s} записів.")
                    if e > 0:
                        st.warning(f"Не знайдено/помилок: {e}")
                        st.caption("Помилки можуть виникати, якщо ПІБ з файлу не знайдено в базі даних (ми не створюємо нових користувачів без авторизації).")
                        
            except Exception as e:
                st.error(f"Error: {e}")

    # --- TAB 3: EXPORT ---
    with tab_export:
        st.markdown("### Експорт списку працівників")
        if st.button("📥 Завантажити Excel"):
            df_ex = pd.DataFrame(workers)
            # Clean up columns for export
            cols_to_export = ['id', 'email', 'full_name', 'role', 'position', 'competence', 'comment', 'operation_types', 'created_at']
            # Filter existing columns
            cols_to_export = [c for c in cols_to_export if c in df_ex.columns]
            
            import io
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df_ex[cols_to_export].to_excel(writer, index=False)
            
            st.download_button(
                "Скачати файл", 
                data=output.getvalue(), 
                file_name="workers_list.xlsx", 
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
