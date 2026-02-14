import streamlit as st
import pandas as pd
from modules.inventory.services import InventoryService
from core.config import UserRole

def render():
    st.header("📦 Склад")
    
    service = InventoryService()
    items = service.get_items()
    
    # --- Metrics ---
    if items:
        total_items = len(items)
        low_stock = sum(1 for i in items if i['quantity'] <= i.get('min_threshold', 0))
        
        c1, c2 = st.columns(2)
        c1.metric("Всього позицій", total_items)
        c2.metric("Закінчуються", low_stock, delta_color="inverse")
    
    tab_list, tab_add = st.tabs(["📋 Список", "➕ Додати"])
    
    with tab_list:
        if not items:
            st.info("Склад порожній.")
        else:
            # Display data
            for item in items:
                with st.expander(f"{item['item_name']} ({item['quantity']} {item['unit']})"):
                    c1, c2 = st.columns([3, 1])
                    with c1:
                        st.write(f"**Кількість:** {item['quantity']} {item['unit']}")
                        st.write(f"**Поріг:** {item['min_threshold']}")
                        
                        if item['quantity'] <= item.get('min_threshold', 0):
                            st.warning("⚠️ Малий залишок!")
                            
                        # Update Quantity Form
                        with st.form(f"update_{item['id']}"):
                            new_qty = st.number_input("Нова кількість", value=float(item['quantity']), key=f"qty_{item['id']}")
                            if st.form_submit_button("Оновити"):
                                service.update_item(item['id'], {"quantity": new_qty})
                                st.rerun()
                                
                    with c2:
                        if st.button("🗑️ Видалити", key=f"del_{item['id']}"):
                            service.delete_item(item['id'])
                            st.rerun()

    with tab_add:
        with st.form("add_item_form"):
            name = st.text_input("Назва")
            c1, c2 = st.columns(2)
            qty = c1.number_input("Кількість", min_value=0.0)
            unit = c2.text_input("Одиниця виміру", value="шт")
            threshold = st.number_input("Мінімальний поріг", value=10)
            
            if st.form_submit_button("Додати"):
                if name:
                    service.add_item({
                        "item_name": name,
                        "quantity": qty,
                        "unit": unit,
                        "min_threshold": threshold
                    })
                    st.success("Додано!")
                    st.rerun()
                else:
                    st.error("Введіть назву.")
