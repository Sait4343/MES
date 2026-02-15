---
name: mes-ui-design
description: Principles and patterns for designing High-Performance MES User Interfaces (ISA-95 compliant, Operator-centric).
---

# MES UI/UX Design Principles

This skill outlines the design philosophy for Manufacturing Execution Systems (MES), focusing on role-based personalization, visual hierarchy, and real-time situational awareness.

## 1. Persona-Based Interfaces

The interface must adapt to the user's role to prevent information overload.

### 👷 Level 1: Operator (Shop Floor)
*   **Goal**: Execution & Safety.
*   **Device**: Tablets, Touch Panels (HMI).
*   **Design Traits**:
    *   **Minimalist**: Show ONLY current task.
    *   **Large Touch Targets**: Buttons > 48px height.
    *   **Visual Instructions**: Step-by-step wizards with images/diagrams.
    *   **Status Indicators**: Traffic light system (🟢 Run, 🟡 Warning, 🔴 Stop).
    *   **Error Handling**: One-tap error reporting.

### 🕵️ Level 2: Supervisor / Dispatcher
*   **Goal**: Monitoring & Quick Reaction.
*   **Device**: Desktop, Wall-mounted Displays.
*   **Design Traits**:
    *   **Bird's Eye View**: Shop floor overview map (Digital Twin lite).
    *   **Real-time Data**: Interactive P&ID (Piping & Instrumentation Diagrams) overlays.
    *   **Flow Maps**: Production flow visualization.
    *   **Drill-down**: Click on a unit -> View detailed history/trends.
    *   **Alerting**: Prioritized alarms list.

### 👔 Level 3: Management
*   **Goal**: Strategy & Efficiency.
*   **Device**: Desktop, Mobile Reports.
*   **Design Traits**:
    *   **Aggregated KPI**: OEE, TEEP, Yield.
    *   **Comparative Charts**: Plan vs. Fact.
    *   **Financials**: Cost per unit, waste cost.
    *   **Trends**: Long-term analysis (Weeks/Months).

## 2. Key UX Principles

1.  **Contextual Relevance**: Information must match the context (Location, Machine, Order).
2.  **Real-Time Capabilities**:
    *   Auto-refresh (no F5 needed).
    *   Critical latency < 200ms.
    *   Update rate: 1-5s for critical parameters.
3.  **Adaptive Design**: Responsive layouts for different screen sizes.
4.  **Color Coding (Standardized)**:
    *   🟢 **Green**: Normal / Running
    *   🟡 **Yellow**: Warning / Idle
    *   🔴 **Red**: Critical / Stopped / Defect
    *   ⚪ **Grey**: Offline / No Data
5.  **Dark Mode**: Optional for low-light control rooms (reduces eye strain).

## 3. Visual Components & Widgets

*   **Interactive P&ID**: SVG/Canvas based diagrams where elements change color based on tag values.
*   **Multi-format Charts**:
    *   *Line*: Trends (Temperature, Pressure).
    *   *Bar*: Production counts (Target vs Actual).
    *   *Gauge*: Instantaneous values (Speed, Load).
    *   *Heatmap*: Defect concentration or downtime frequency.
*   **Alerting System**: Popups (Toast) for critical alarms, Banner for persistent warnings.
*   **Drag-and-Drop**: Allow Supervisors to customize their dashboard layout.

## 4. Technical Implementation Recommendations

### Stack References
*   **Backend**: Python (FastAPI/Django) or Node.js.
*   **Real-time**: MQTT (Machine data), WebSockets (UI push).
*   **Database**: PostgreSQL (Relational), InfluxDB (Time-series).
*   **Frontend**: React/Vue (Standard) or **Streamlit** (Rapid Prototyping/Internal Tools).

### Streamlit Adaptation (Specific to this project)
*   **Auto-refresh**: Use `st_autorefresh` or `st.empty()` loops with `time.sleep` (for simple cases).
*   **Visuals**: Use `Plotly` for interactive charts.
*   **Layout**: Use `st.columns` and custom CSS for "Cards".
*   **State**: Use `st.session_state` to track Role/Context.
*   **Navigation**: `st.page_link` for role-based menus.

## 5. Integration Points (ISA-95)
*   **ERP**: Order import, Material consumption, Finished goods reporting.
*   **SCADA**: Tag readings (Temp, Speed, Count).
*   **WMS**: Material location, Picking requests.
*   **QMS**: Lab results, Quality holds.
