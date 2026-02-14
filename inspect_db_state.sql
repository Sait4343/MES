-- ==========================================
-- 🕵️ Deep Database Inspection
-- ==========================================

-- 1. List ALL Triggers on 'orders' table
select 
    trigger_schema,
    trigger_name,
    event_manipulation,
    action_statement,
    action_orientation,
    action_timing
from information_schema.triggers
where event_object_table = 'orders';

-- 2. List ALL Columns in 'production_steps' to check types
select 
    column_name, 
    data_type, 
    udt_name
from information_schema.columns
where table_name = 'production_steps';

-- 3. List ALL custom Types/Enums in the database
select 
    n.nspname as schema_name,
    t.typname as type_name,
    e.enumlabel as enum_value
from pg_type t
join pg_enum e on t.oid = e.enumtypid
join pg_namespace n on n.oid = t.typnamespace
where n.nspname = 'public';
