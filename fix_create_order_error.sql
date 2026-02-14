-- ==========================================
-- 🛠️ Fix Order Creation Error (step_name type)
-- ==========================================

-- 1. Ensure `production_steps.step_name` is TEXT (not a custom type)
alter table public.production_steps 
alter column step_name type text using step_name::text;

-- 2. Redefine the trigger function to be explicit about text types
-- This overwrites the existing function that might be referencing the missing type
create or replace function public.create_default_steps()
returns trigger as $$
declare
  -- Explicitly define as TEXT array
  steps text[] := array['cutting', 'basting', 'sewing', 'overlock', 'completing', 'edging', 'finishing', 'fixing', 'packing'];
  s text;
begin
  foreach s in array steps
  loop
    insert into public.production_steps (order_id, step_name, status)
    values (new.id, s, 'not_started')
    on conflict (order_id, step_name) do nothing;
  end loop;
  return new;
end;
$$ language plpgsql;

-- 3. Cleanup: Drop the custom type if it exists (Optional safety)
do $$ begin
    drop type if exists public.step_name;
exception
    when others then null;
end $$;
