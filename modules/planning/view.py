import streamlit as st
import pandas as pd
from modules.planning.services import PlanningService
from core.config import StepStatus

def render():
    st.header("📅 Виробнича таблиця (Excel)")
    
    service = PlanningService()
    
    # Reload button
    if st.button("🔄 Оновити дані"):
        st.cache_data.clear()
        st.rerun()

    # Fetch Data
    df, step_id_map = service.get_planning_dataframe()
    
    if df.empty:
        st.info("Немає даних для відображення.")
        return

    # User Role Check
    user_role = st.session_state.get("role", "viewer")
    is_viewer = user_role == "viewer"

    # Configure Columns for Data Editor
    # Steps get Selectbox (Dropdown)
    step_options = [s.value for s in StepStatus]
    
    column_config = {
        "id": None, # Hide ID
        "Order #": st.column_config.TextColumn("№ Замовлення", disabled=True),
        "Product": st.column_config.TextColumn("Виріб", disabled=True),
        "Article": st.column_config.TextColumn("Артикул"),
        "Qty": st.column_config.NumberColumn("К-сть"),
        "Contractor": st.column_config.TextColumn("Підрядник"),
        "Start Date": st.column_config.DateColumn("Дата початку", format="DD.MM.YYYY"),
        "Ship Date": st.column_config.DateColumn("Дата відвантаження", format="DD.MM.YYYY"),
        "Comment": st.column_config.TextColumn("Коментар"),
    }
    
    # Add config for step columns
    for step in service.step_order:
        col_title = step.title()
        column_config[col_title] = st.column_config.SelectboxColumn(
            col_title,
            options=step_options,
            required=True,
            width="medium"
        )
    
    # Render Editor
    # If viewer, disable all columns or just use st.dataframe
    if is_viewer:
        st.dataframe(df, hide_index=True, use_container_width=True, height=600)
        st.info("ℹ️ Режим перегляду: Ви не можете вносити зміни.")
        return

    edited_df = st.data_editor(
        df,
        column_config=column_config,
        hide_index=True,
        use_container_width=True,
        num_rows="fixed",
        key="planning_table",
        height=600
    )
    
    # Check for changes
    # st.data_editor returns the new state. We need to find what changed.
    # Actually, simpler way with key: st.session_state["planning_table"] contains "edited_rows"
    
    if "planning_table" in st.session_state:
        changes = st.session_state["planning_table"].get("edited_rows", {})
        
        if changes:
            # Save button appears if there are changes (auto-save logic can be tricky with reruns)
            # But st.data_editor updates state immediately.
            # To do "Instant Save", we should process `changes` immediately.
            # However, `changes` is a dict of index -> {col: val}.
            
            with st.spinner("Збереження змін..."):
                service.save_changes(changes, df, step_id_map)
                
            # We don't want to rerun immediately on every keystroke if it causes lag, 
            # but for "Instant", we should.
            # However, `changes` persists until we explicitly clear it or reload?
            # Actually data_editor output `edited_df` is the new truth.
            # The `changes` in session state are just the delta for this interaction.
            
            st.success("Зміни збережено!")
            # st.rerun() # This might cause loop if not careful.
            
            # Better pattern: Use on_change callback if possible, or just process here.
            # Since we wrote to DB, next fetch will have new data.
            # We should clear cache.
            st.cache_data.clear()
