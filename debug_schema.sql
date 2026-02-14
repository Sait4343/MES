-- ==========================================
-- 🐞 Debug Schema (Triggers & Functions)
-- ==========================================

-- 1. List all triggers on the 'orders' table
select 
    trigger_name, 
    event_manipulation, 
    action_statement, 
    action_orientation, 
    action_timing
from information_schema.triggers
where event_object_table = 'orders';

-- 2. List definition of the function 'create_default_steps'
select 
    routine_name, 
    routine_definition
from information_schema.routines
where routine_name = 'create_default_steps';

-- 3. Check column type of 'production_steps.step_name'
select 
    column_name, 
    data_type, 
    udt_name
from information_schema.columns
where table_name = 'production_steps' 
and column_name = 'step_name';
