# 🏭 Digital Production Planning System

## Overview
A web-based production planning system built with Streamlit and Supabase to replace Excel workflows.

## Features
- **Dashboard**: Real-time production statistics.
- **Orders**: Create and manage orders.
- **Planning**: Track production steps (Kanban/List view).
- **Auth**: Secure login with Role-Based Access Control (Admin, Manager, Worker).

## Installation

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configuration**:
   Ensure `.streamlit/secrets.toml` is configured with your Supabase credentials:
   ```toml
   [secrets]
   SUPABASE_URL = "your_url"
   SUPABASE_KEY = "your_key"
   ```

3. **Run the App**:
   ```bash
   streamlit run app.py
   ```

## Folder Structure
- `core/`: Config, Database, Auth
- `modules/`: Feature logic (Dashboard, Orders, Planning)
- `ui/`: Shared UI components
