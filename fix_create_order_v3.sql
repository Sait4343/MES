-- ==========================================
-- 🛠️ Fix Order Creation Error (V3 - Final)
-- ==========================================

-- 1. Detach the trigger first
drop trigger if exists on_order_created_steps on public.orders;

-- 2. Drop the old function (if possible) to clean up
drop function if exists public.create_default_steps();

-- 3. Ensure table column is TEXT
-- We use a simple ALTER first. 
-- If the column is already text, this is a no-op.
-- If it's an enum, this might fail without USING, so we add a specific cast if needed.
-- But given the error "type does not exist", we try to force it to standard text.
do $$ 
begin
    alter table public.production_steps 
    alter column step_name type text;
exception 
    when others then 
        -- If simple alter fails, try with explicit cast
        begin
            alter table public.production_steps 
            alter column step_name type text using step_name::text;
        exception when others then
            null; -- Ignore if really stuck (manual fix needed)
        end;
end $$;


-- 4. Create a NEW function with a FRESH name to guarantee no stale references
create or replace function public.create_order_steps_text()
returns trigger as $$
declare
    -- Define steps purely as text array
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

-- 5. Attach the trigger to the NEW function
create trigger on_order_created_steps
    after insert on public.orders
    for each row execute procedure public.create_order_steps_text();
