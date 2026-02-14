-- ==========================================
-- 🛠️ Fix Order Creation Error V2 (Robust)
-- ==========================================

-- 1. DROP EVERYTHING related to the problematic trigger first
-- This ensures we don't have any stale references
drop trigger if exists on_order_created_steps on public.orders;
drop function if exists public.create_default_steps();

-- 2. Ensure table column is TEXT
alter table public.production_steps 
alter column step_name type text using step_name::text;

-- 3. Re-create the function with explicit TEXT types
create or replace function public.create_default_steps()
returns trigger as $$
declare
  -- Define steps as text array explicitly
  steps text[] := array['cutting', 'basting', 'sewing', 'overlock', 'completing', 'edging', 'finishing', 'fixing', 'packing'];
  s text;
begin
  foreach s in array steps
  loop
    -- Insert with explicit text casting just in case
    insert into public.production_steps (order_id, step_name, status)
    values (new.id, s::text, 'not_started')
    on conflict (order_id, step_name) do nothing;
  end loop;
  return new;
end;
$$ language plpgsql;

-- 4. Re-attach the trigger
create trigger on_order_created_steps
  after insert on public.orders
  for each row execute procedure public.create_default_steps();
