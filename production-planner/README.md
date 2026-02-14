# MES Production Planner

A production planning web system built with **Streamlit** and **Supabase**.

## Features
- **Role-based Access**: Admin, Manager, Worker.
- **Order Management**: Excel-like editable grid for tracking orders.
- **Production Steps**: Track status (Not Started, In Progress, Done, Problem) for each production step (Cutting, Sewing, etc.).
- **Visual Calendar**: Gantt chart for production schedule.
- **Admin Tools**: Import/Export orders via Excel.

## Setup Guide

### 1. Prerequisites
- Python 3.8+
- Supabase Account

### 2. Installation
```bash
pip install -r requirements.txt
```

### 3. Database Setup
1. Create a new project in [Supabase](https://supabase.com/).
2. Go to the **SQL Editor** in your Supabase dashboard.
3. Copy the contents of `setup_db.sql` and run it. This will create the necessary tables, enums, RLS policies, and triggers.

### 4. Configuration
Create a file named `.streamlit/secrets.toml` in the `d:/MES/production-planner` directory (create the folder if it doesn't exist):

```toml
[general]
SUPABASE_URL = "your-supabase-url"
SUPABASE_KEY = "your-supabase-anon-key"
```

### 5. Running the Application
```bash
streamlit run d:/MES/production-planner/main.py
```

## User Roles
By default, new users sign up as **Workers**. To promote a user to **Admin**:
1. Sign up a new user via the App or Supabase Auth.
2. In Supabase SQL Editor, run:
```sql
update profiles set role = 'admin' where email = 'user@example.com';
```

## Project Structure
- `main.py`: Entry point and navigation.
- `auth.py`: Authentication logic.
- `utils.py`: Database helper functions.
- `pages/`: Application pages.
    - `01_Orders.py`: Main grid view.
    - `02_Order_Details.py`: Single order timeline.
    - `03_Calendar.py`: Visual schedule.
    - `04_Admin.py`: Data import/export.
