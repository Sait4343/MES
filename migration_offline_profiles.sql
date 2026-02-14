-- ==========================================
-- 🔓 Allow Offline Workers (Drop Strict Auth FK)
-- ==========================================

-- This script modifies the profiles table to allow creating workers
-- who do not have a Supabase Auth account (e.g. imported from Excel).

do $$
declare
    con_name text;
begin
    -- Find the Foreign Key constraint name for profiles -> auth.users
    select constraint_name into con_name
    from information_schema.table_constraints
    where table_name = 'profiles'
      and constraint_type = 'FOREIGN KEY';
      
    if found then
        execute format('alter table public.profiles drop constraint %I', con_name);
    end if;

    -- Ensure id has a default value generator if not present
    alter table public.profiles alter column id set default uuid_generate_v4();
    
end $$;
