import streamlit as st
from datetime import datetime

# --- 1. CSS & STYLING ---
def load_custom_css():
    """Injects global CSS for the MES Design System."""
    st.markdown("""
        <style>
        /* Global Font (Optional, usually Inter or Roboto via Streamlit theme) */
        
        /* KPI Card Styling */
        div.kpi-card {
            background-color: #f8f9fa;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            text-align: center;
        }
        div.kpi-card h3 {
            margin: 0;
            font-size: 1.2rem;
            color: #6c757d;
        }
        div.kpi-card h2 {
            margin: 10px 0;
            font-size: 2.5rem;
            color: #212529;
            font-weight: 700;
        }
        div.kpi-card span.delta {
            font-size: 0.9rem;
            font-weight: 600;
        }
        
        /* Task Card Styling (Operator) */
        div.task-card {
            background-color: #ffffff;
            border: 1px solid #dee2e6;
            border-left: 5px solid #007bff; /* Default Blue */
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 10px;
        }
        div.task-card h4 {
            margin: 0 0 5px 0;
            color: #343a40;
        }
        div.task-card p {
            margin: 0;
            color: #6c757d;
            font-size: 0.9rem;
        }
        
        /* Status Badges */
        .badge {
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.8rem;
            font-weight: bold;
            color: white;
        }
        .bg-green { background-color: #28a745; }
        .bg-yellow { background-color: #ffc107; color: #212529; }
        .bg-red { background-color: #dc3545; }
        .bg-blue { background-color: #007bff; }
        .bg-grey { background-color: #6c757d; }
        
        /* Large Touch Buttons */
        .stButton button {
            min-height: 45px; /* Taller for touch */
        }
        </style>
    """, unsafe_allow_html=True)

# --- 2. WIDGETS ---

def render_kpi_card(title: str, value: str, delta: str = None, color: str = "green"):
    """
    Renders a KPI card with HTML/CSS.
    Streamlit's native st.metric is good, but this allows custom styling background.
    """
    delta_html = ""
    if delta:
        delta_color = "green" if color == "green" else "red" # Simple logic
        arrow = "↑" if not delta.startswith("-") else "↓"
        delta_html = f"<span class='delta' style='color:{delta_color}'>{arrow} {delta}</span>"
        
    html = f"""
    <div class='kpi-card'>
        <h3>{title}</h3>
        <h2>{value}</h2>
        {delta_html}
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

def render_status_badge(status: str):
    """Returns HTML for a colored badge based on standard statuses."""
    # Map status to color class
    color_map = {
        "done": "bg-green",
        "finished": "bg-green",
        "in_progress": "bg-blue",
        "started": "bg-blue",
        "pending": "bg-grey",
        "not_started": "bg-grey",
        "problem": "bg-red",
        "paused": "bg-yellow"
    }
    css_class = color_map.get(status, "bg-grey")
    label = status.replace("_", " ").upper()
    
    st.markdown(f"<span class='badge {css_class}'>{label}</span>", unsafe_allow_html=True)

def render_task_card(task: dict, on_action=None):
    """
    Renders a rich task card for operators.
    Args:
        task: Dict containing task details (from DB).
        on_action: Callback function (not used directly in Streamlit pure UI, but logically).
    """
    # Extract details
    op_name = task.get('operations_catalog', {}).get('operation_key', 'Unknown Op')
    product = task.get('orders', {}).get('product_name', 'Unknown Product')
    qty = task.get('quantity', 0)
    status = task.get('status', 'pending')
    
    # Determine Border Color
    border_color = "#6c757d" # Grey
    if status == 'in_progress': border_color = "#007bff" # Blue
    elif status == 'done': border_color = "#28a745" # Green
    elif status == 'problem': border_color = "#dc3545" # Red
    
    st.markdown(f"""
    <div style='
        background-color: white;
        border: 1px solid #dee2e6;
        border-left: 8px solid {border_color};
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 10px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    '>
        <h4 style='margin:0; font-size:1.1rem;'>{op_name}</h4>
        <p style='color:#6c757d; font-weight:600;'>{product}</p>
        <div style='display:flex; justify-content:space-between; margin-top:5px;'>
            <span>Qty: <strong>{qty}</strong></span>
            <span>Status: <strong>{status.upper()}</strong></span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Buttons are rendered OUTSIDE the HTML block because Streamlit buttons can't be in HTML
    # The caller of this function will handle buttons below the card visuals.
