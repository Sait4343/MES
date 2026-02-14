-- ==========================================
-- 🔧 Fix Workers Relationships (Explicit FK Names)
-- ==========================================

-- 1. Drop unknown/auto-generated constraints to avoid duplicates/confusion
do $$
declare
    r record;
begin
    -- Find constraints on created_by
    for r in select constraint_name 
             from information_schema.key_column_usage 
             where table_name = 'profiles' and column_name = 'created_by' 
             and constraint_name != 'profiles_created_by_fkey' -- Don't drop if already correct
    loop
        execute format('alter table public.profiles drop constraint %I', r.constraint_name);
    end loop;

    -- Find constraints on updated_by
    for r in select constraint_name 
             from information_schema.key_column_usage 
             where table_name = 'profiles' and column_name = 'updated_by'
             and constraint_name != 'profiles_updated_by_fkey'
    loop
        execute format('alter table public.profiles drop constraint %I', r.constraint_name);
    end loop;
end $$;

-- 2. Add Explicit Named Constraints
-- These names (profiles_created_by_fkey) will be used in the API call
do $$
begin
    if not exists (select 1 from information_schema.table_constraints where constraint_name = 'profiles_created_by_fkey') then
        alter table public.profiles 
        add constraint profiles_created_by_fkey 
        foreign key (created_by) references public.profiles(id);
    end if;

    if not exists (select 1 from information_schema.table_constraints where constraint_name = 'profiles_updated_by_fkey') then
        alter table public.profiles 
        add constraint profiles_updated_by_fkey 
        foreign key (updated_by) references public.profiles(id);
    end if;
end $$;

-- 3. Notify PostgREST to reload schema
NOTIFY pgrst, 'reload';
