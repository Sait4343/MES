---
name: streamlit-pro
description: Advanced Streamlit patterns, caching strategies, layout optimization, and state management.
---

# Production-Ready Streamlit

When building Streamlit applications, prioritize performance and maintainability:

### 1. State Management
- Use `st.session_state` to persist data between reruns.
- Initialize all session state variables at the top of the script using a helper function `init_state()`.
- Avoid modifying `st.session_state` directly inside widgets if possible; use callbacks (`on_change`).

### 2. Caching & Performance
- **Data Loading**: ALWAYS use `@st.cache_data` for data fetching functions (CSV loading, API calls, SQL queries).
- **Resources**: Use `@st.cache_resource` for heavy objects like ML models or database connections.
- **TTL**: Set `ttl` parameters for cache validation to prevent stale data.

### 3. Layout & UX
- **Sidebar**: Use `st.sidebar` for filters and global controls ONLY. Main content goes to the main area.
- **Columns**: Use `st.columns` to create dense, dashboard-like layouts instead of vertical stacking.
- **Progress**: Always show `st.spinner()` or progress bars during long operations.

### 4. Code Structure
- Split code into `pages/` for multi-page apps.
- Move logic (data processing, API calls) into a separate `utils.py` file. Keep the main UI file clean.
