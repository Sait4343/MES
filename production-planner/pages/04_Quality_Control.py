import streamlit as st
import pandas as pd
import plotly.express as px
from modules.orders.services import OrderService
from modules.quality.services import QualityService

st.set_page_config(page_title="Quality Control", page_icon="🔍", layout="wide")

st.title("🔍 Контроль Якості (Quality Control)")

# Services
order_service = OrderService()
quality_service = QualityService()

# Tabs
tab1, tab2 = st.tabs(["📝 Реєстрація Браку", "📊 Аналітика"])

with tab1:
    st.markdown("### Реєстрація Невідповідності")
    
    # 1. Select Order
    orders = order_service.get_orders()
    order_options = {o['id']: f"{o['order_number']} - {o['customer_name']}" for o in orders}
    
    selected_order_id = st.selectbox("Оберіть Замовлення", options=list(order_options.keys()), format_func=lambda x: order_options[x])
    
    if selected_order_id:
        # 2. Select Operation (Where defect was found)
        ops = order_service.get_order_operations(selected_order_id)
        if ops:
            op_options = {op['id']: f"{op['sort_order']}. {op.get('operations_catalog', {}).get('operation_key')} ({op.get('sections', {}).get('name')})" for op in ops}
            selected_op_id = st.selectbox("Оберіть Операцію", options=list(op_options.keys()), format_func=lambda x: op_options[x])
            
            with st.form("defect_form"):
                col1, col2 = st.columns(2)
                with col1:
                    defect_type = st.selectbox("Тип Дефекту", ["Scrap (Брак)", "Rework (На допрацювання)", "Observation (Зауваження)"])
                    quantity = st.number_input("Кількість", min_value=1, value=1)
                
                with col2:
                    reason = st.text_input("Причина", placeholder="Напр. Подряпина, невірний розмір")
                
                submitted = st.form_submit_button("🔴 Зареєструвати Дефект")
                
                if submitted:
                    res = quality_service.log_defect(selected_op_id, defect_type, quantity, reason)
                    if res:
                        st.success("Дефект зареєстровано!")
        else:
            st.warning("В цьому замовленні ще немає операцій.")

with tab2:
    st.markdown("### Аналіз Якості")
    df_stats = quality_service.get_defects_stats()
    
    if not df_stats.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Кількість дефектів за типом**")
            fig_type = px.pie(
                df_stats, 
                values='quantity', 
                names='defect_type', 
                hole=0.4,
                labels={'quantity': 'Кількість', 'defect_type': 'Тип дефекту'}
            )
            fig_type.update_layout(font=dict(family="Arial, sans-serif"))
            st.plotly_chart(fig_type, use_container_width=True)
            
        with col2:
            st.markdown("**ТОП Причин Дефектів**")
            fig_reason = px.bar(
                df_stats.groupby('reason')['quantity'].sum().reset_index(), 
                x='reason', 
                y='quantity', 
                color='quantity',
                labels={'reason': 'Причина', 'quantity': 'Кількість'}
            )
            fig_reason.update_layout(font=dict(family="Arial, sans-serif"))
            fig_reason.update_xaxes(title_text="Причина")
            fig_reason.update_yaxes(title_text="Кількість")
            st.plotly_chart(fig_reason, use_container_width=True)
            
        st.dataframe(df_stats, use_container_width=True)
    else:
        st.info("Ще немає даних про дефекти.")
