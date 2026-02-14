import streamlit as st
import pandas as pd
from modules.orders.services import OrderService
from modules.orders.impex import ImpexService
from modules.sections.services import SectionsService
from core.config import UserRole

def render():
    st.header("📦 Керування замовленнями")
    
    # Initialize Service
    service = OrderService()
    sections_service = SectionsService()
    impex = ImpexService()

    # Handle Navigation State
    if "selected_order_id" not in st.session_state:
        st.session_state.selected_order_id = None

    # --- DETAIL VIEW (Planning) ---
    if st.session_state.selected_order_id:
        render_detail_view(service, sections_service)
    else:
        render_list_view(service, impex)

def render_list_view(service, impex):
    tab_list, tab_new, tab_import, tab_export = st.tabs(["📋 Список", "➕ Нове замовлення", "📥 Імпорт", "📤 Експорт"])
    
    with tab_list:
        orders = service.get_orders()
        if not orders:
            st.info("Замовлень поки немає.")
        else:
            df = pd.DataFrame(orders)
            
            # Select Order logic
            order_options = {o['id']: f"{o['order_number']} | {o['product_name']}" for o in orders}
            selected_id = st.selectbox("🔍 Оберіть замовлення для планування:", options=list(order_options.keys()), format_func=lambda x: order_options[x], index=None, placeholder="Оберіть замовлення...")
            
            if selected_id:
                if st.button("📝 Відкрити планування замовлення"):
                    st.session_state.selected_order_id = selected_id
                    st.rerun()

            st.dataframe(
                df, 
                column_config={
                    "order_number": "№",
                    "product_name": "Виріб",
                    "quantity": "К-ть",
                    "created_at": st.column_config.DatetimeColumn(
                        "Створено",
                        format="YYYY-MM-DD HH:mm"
                    ),
                    "shipping_date": st.column_config.DateColumn("Відвантаження", format="YYYY-MM-DD"),
                    "start_date": st.column_config.DateColumn("Початок", format="YYYY-MM-DD"),
                    "preparation_date": st.column_config.DateColumn("Підготовка", format="YYYY-MM-DD"),
                    "updated_at": st.column_config.DatetimeColumn(
                        "Оновлено",
                        format="YYYY-MM-DD HH:mm"
                    ),
                    "contractor": "Контрагент",
                },
                column_order=["order_number", "product_name", "quantity", "contractor", "created_at", "shipping_date", "start_date", "preparation_date"],
                use_container_width=True,
                hide_index=True
            )

    # --- TAB 2: NEW ORDER (Same as before) ---
    with tab_new:
        render_new_order_form(service)

    # --- TAB 3: IMPORT (Same as before) ---
    with tab_import:
        render_import_tab(impex)

    # --- TAB 4: EXPORT ---
    with tab_export:
        if st.button("🔄 Згенерувати експорт"):
            data = impex.export_orders()
            if data:
                st.download_button("📥 Завантажити", data, "orders.xlsx")

def render_detail_view(service, sections_service):
    # Fetch Order Data
    order_id = st.session_state.selected_order_id
    # We fetch all and find one (inefficient but safe for MVP) or add get_order_by_id
    orders = service.get_orders()
    order = next((o for o in orders if o['id'] == order_id), None)
    
    if not order:
        st.error("Замовлення не знайдено.")
        if st.button("⬅ Назад"):
            st.session_state.selected_order_id = None
            st.rerun()
        return

    # Header
    c1, c2 = st.columns([1, 4])
    if c1.button("⬅ Назад до списку"):
        st.session_state.selected_order_id = None
        st.rerun()
    
    st.title(f"Замовлення: {order['order_number']}")
    st.caption(f"Виріб: {order['product_name']} | Артикул: {order['article']} | Кількість: {order['quantity']}")
    
    st.divider()
    
    # ---------------- PLANNING UI ----------------
    st.subheader("📅 Планування виробництва (Маршрут)")
    
    # 1. Existing Planned Ops
    planned_ops = service.get_order_operations(order_id)
    
    if planned_ops:
        st.write("Current Plan:")
        df_plan = pd.DataFrame(planned_ops)
        
        # Flatten relations for display
        if 'operations_catalog' in df_plan.columns:
             df_plan['Op Name'] = df_plan['operations_catalog'].apply(lambda x: x.get('operation_key') if x else 'custom')
        if 'sections' in df_plan.columns:
             df_plan['Section'] = df_plan['sections'].apply(lambda x: x.get('name') if x else '?')
        if 'profiles' in df_plan.columns:
             df_plan['Worker'] = df_plan['profiles'].apply(lambda x: x.get('full_name') if x else '-')

        st.dataframe(
            df_plan,
            column_config={
                "id": None,
                "created_at": None,
                "operations_catalog": None, "sections": None, "profiles": None, "order_id": None,
                "Section": "Дільниця",
                "Op Name": "Операція",
                "norm_time_per_unit": st.column_config.NumberColumn("Норма (1 шт)", format="%.2f хв"),
                "quantity": "К-ть",
                "total_estimated_time": st.column_config.NumberColumn("Заг. час (хв)", format="%.1f"),
                "Worker": "Працівник",
                "status": "Статус"
            },
            hide_index=True,
            use_container_width=True
        )
        
        total_time = df_plan['total_estimated_time'].sum() if not df_plan.empty else 0
        st.success(f"⏱️ Загальний розрахунковий час: {total_time:.1f} хв ({(total_time/60):.1f} год)")
    else:
        st.info("Маршрут ще не сплановано.")
        
    st.divider()
    st.write("#### ➕ Додати етап виробництва")
    
    with st.container(border=True):
        # Step 1: Select Section
        all_sections = sections_service.get_all_sections()
        if all_sections.empty:
            st.error("Спочатку створіть Дільниці.")
        else:
            sec_dict = {s['id']: s['name'] for s in all_sections.to_dict('records')}
            selected_sec_id = st.selectbox("1. Дільниця", options=list(sec_dict.keys()), format_func=lambda x: sec_dict[x])
            
            # Step 2: Select Operation from Catalog (filtered by Section or All?? User said 'pull processes necessary')
            # Assuming operations_catalog has a 'section' text field that matches Section Name?
            # Or we filter loosely. Let's fetch all for now or filter if we can map.
            # Ideally: available_ops = service.get_available_operations(section_name)
            
            current_sec_name = sec_dict[selected_sec_id]
            
            # Fetch catalog
            # We filter locally for MVP simplicity since service returns all
            all_ops = service.get_available_operations() 
            # Filter where 'section' matches selected section name
            filtered_ops = [op for op in all_ops if op.get('section') == current_sec_name]
            
            if not filtered_ops:
                st.warning(f"Немає операцій для дільниці '{current_sec_name}'. Додайте їх у 'Операції'.")
            else:
                op_dict = {op['id']: f"{op.get('operation_key')} | {op.get('article')} (Norm: {op.get('norm_time')})" for op in filtered_ops}
                selected_op_id = st.selectbox("2. Операція", options=list(op_dict.keys()), format_func=lambda x: op_dict[x])
                
                selected_op = next(op for op in filtered_ops if op['id'] == selected_op_id)
                norm_time = selected_op.get('norm_time', 0)
                st.info(f"Норма часу: {norm_time} хв/шт")
                
                # Step 3: Quantity
                qty = st.number_input("3. Кількість", value=order['quantity'], min_value=1)
                
                calc_time = norm_time * qty
                st.write(f"📊 Розрахунковий час: **{calc_time:.2f} хв**")
                
                # Step 4: Available Workers
                available_workers = service.fetch_section_workers(current_sec_name)
                worker_options = {w['id']: w['full_name'] for w in available_workers}
                
                selected_worker_id = st.selectbox(
                    f"4. Призначити працівника (Доступно: {len(available_workers)})", 
                    options=[None] + list(worker_options.keys()),
                    format_func=lambda x: worker_options[x] if x else "--- Без призначення ---"
                )

                if st.button("Додати етап"):
                    new_op_data = {
                        "order_id": order_id,
                        "operation_catalog_id": selected_op_id,
                        "section_id": selected_sec_id,
                        "assigned_worker_id": selected_worker_id,
                        "operation_name": selected_op.get('operation_key'), # Snapshot
                        "quantity": qty,
                        "norm_time_per_unit": norm_time,
                        # total_time is generated
                        "status": "not_started"
                    }
                    res, err = service.create_order_operation(new_op_data)
                    if res:
                        st.success("Етап додано!")
                        st.rerun()
                    else:
                        st.error(f"Помилка: {err}")

# Helpers for other tabs (kept simple)
def render_new_order_form(service):
    user_role = st.session_state.role
    if user_role not in [UserRole.ADMIN, UserRole.MANAGER]:
        st.info("🔒 Створення замовлень доступне тільки для менеджерів та адміністраторів.")
        return
    
    with st.form("new_order_form"):
        c1, c2 = st.columns(2)
        with c1:
            order_number = st.text_input("Номер замовлення (Унікальний)*")
            product_name = st.text_input("Назва виробу*")
            article = st.text_input("Артикул")
        with c2:
            quantity = st.number_input("Кількість*", min_value=1, value=1)
            contractor = st.text_input("Контрагент")
            
            # Dates
            c_d1, c_d2, c_d3 = st.columns(3)
            with c_d1:
                start_date = st.date_input("Дата початку", value=None)
            with c_d2:
                preparation_date = st.date_input("Дата підготовки (крою)", value=None)
            with c_d3:
                shipping_date = st.date_input("Дата відвантаження", value=None)
        
        comment = st.text_area("Коментар")
        
        if st.form_submit_button("Створити замовлення"):
            if not order_number or not product_name:
                st.error("Обов'язкові поля!")
            else:
                data = {
                    "order_number": order_number,
                    "product_name": product_name,
                    "article": article,
                    "quantity": quantity,
                    "contractor": contractor,
                    "comment": comment
                }
                
                # Handle dates (isoformat if selected, else None)
                if start_date: data["start_date"] = start_date.isoformat()
                if preparation_date: data["preparation_date"] = preparation_date.isoformat()
                if shipping_date: data["shipping_date"] = shipping_date.isoformat()
                res = service.create_order(data)
                if res:
                    st.success("Замовлення створено!")

def render_import_tab(impex):
    st.subheader("Масове завантаження")
    
    if st.session_state.role not in [UserRole.ADMIN, UserRole.MANAGER]:
        st.info("🔒 Імпорт доступний тільки для менеджерів та адміністраторів.")
        return

    # Use a key in session state for the uploader to allow resetting
    if "import_uploader_key" not in st.session_state:
        st.session_state["import_uploader_key"] = 0

    uploaded_file = st.file_uploader(
        "Оберіть файл Excel (.xlsx)", 
        type=['xlsx', 'xls'],
        key=f"uploader_{st.session_state['import_uploader_key']}"
    )
    
    if uploaded_file:
        try:
            xls = pd.ExcelFile(uploaded_file)
            sheet = st.selectbox("Оберіть аркуш (Sheet)", xls.sheet_names)
            
            df_raw = pd.read_excel(uploaded_file, sheet_name=sheet)
            
            st.write("#### Попередній перегляд (перші 5 рядків)")
            st.dataframe(df_raw.head())
            
            st.divider()
            st.write("#### Співставлення колонок")
            
            # Define DB columns we want to map
            db_fields = {
                "order_number": "Номер замовлення (Required)",
                "product_name": "Назва виробу (Required)",
                "quantity": "Кількість (Required)",
                "article": "Артикул",
                "contractor": "Контрагент",
                "start_date": "Дата початку",
                "preparation_date": "Дата підготовки",
                "shipping_date": "Дата відвантаження",
                "comment": "Коментар"
            }
            
            excel_headers = ["(Пропустити)"] + list(df_raw.columns)
            cols_map = {}
            
            # Create mapping selectors
            c_cols = st.columns(2)
            for i, (db_key, db_label) in enumerate(db_fields.items()):
                # Try to auto-match using Impex aliases
                default_idx = 0
                
                # Get possible aliases for this DB field from ImpexService
                aliases = impex.get_field_aliases(db_key)
                
                # Also try matching the label itself if not in aliases
                search_terms = aliases + [db_label]
                
                for idx, header in enumerate(excel_headers):
                    if idx == 0: continue # Skip 'skip' option
                    h_clean = header.lower().strip()
                    # Check if any alias is in the header
                    if any(alias.lower() in h_clean for alias in search_terms):
                         default_idx = idx
                         break
                
                with c_cols[i % 2]:
                    cols_map[db_key] = st.selectbox(f"Поле БД: {db_label}", excel_headers, index=default_idx, key=f"map_{db_key}")
            
            if st.button("🚀 Імпортувати замовлення"):
                with st.spinner("Імпорт даних..."):
                    # Call new import method
                    s, f = impex.import_orders_from_df(df_raw, cols_map)
                
                if s > 0:
                    st.success(f"✅ Успішно імпортовано: {s}")
                    # Increment key to reset uploader
                    st.session_state["import_uploader_key"] += 1
                    st.rerun()
                if f > 0:
                    if s == 0:
                        st.error(f"❌ Не вдалося імпортувати: {f} (Можливо дублікати номерів або помилки даних)")
                    else:
                        st.warning(f"⚠️ Пропущено/Помилок: {f}")
                        
                st.cache_data.clear()
                
        except Exception as e:
            st.error(f"Помилка читання файлу: {e}")
