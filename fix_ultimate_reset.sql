-- ==========================================
-- ☢️ ULTIMATE RESET: Drop ALL Order Triggers
-- ==========================================

BEGIN;

-- 1. Aggressively Drop ALL Triggers on 'orders' table
-- We use dynamic SQL to find any trigger attached to 'orders' and kill it.
-- This handles cases where old triggers might have different names (e.g. "on_new_order", "trigger_step_creation" etc)
DO $$ 
DECLARE 
    r RECORD;
BEGIN 
    FOR r IN (SELECT trigger_name FROM information_schema.triggers WHERE event_object_table = 'orders') 
    LOOP 
        EXECUTE 'DROP TRIGGER IF EXISTS ' || quote_ident(r.trigger_name) || ' ON public.orders CASCADE'; 
    END LOOP; 
END $$;

-- 2. Drop ALL related functions (Cleanup)
DROP FUNCTION IF EXISTS public.create_default_steps() CASCADE;
DROP FUNCTION IF EXISTS public.create_order_steps_text() CASCADE;
DROP FUNCTION IF EXISTS public.create_order_steps_v4() CASCADE;
DROP FUNCTION IF EXISTS public.handle_new_order() CASCADE; -- Just in case

-- 3. Ensure Table Column is TEXT (Again, to be safe)
ALTER TABLE public.production_steps 
ALTER COLUMN step_name TYPE text USING step_name::text;

-- 4. Clean Custom Type (Again)
DROP TYPE IF EXISTS public.step_name;

-- 5. Recreate Logic (Version 5 - Clean)
CREATE OR REPLACE FUNCTION public.create_order_steps_safe()
RETURNS trigger AS $$
DECLARE
    -- No custom types, just text
    steps text[] := ARRAY['cutting', 'basting', 'sewing', 'overlock', 'completing', 'edging', 'finishing', 'fixing', 'packing'];
    s text;
BEGIN
    FOREACH s IN ARRAY steps
    LOOP
        INSERT INTO public.production_steps (order_id, step_name, status)
        VALUES (NEW.id, s, 'not_started')
        ON CONFLICT (order_id, step_name) DO NOTHING;
    END LOOP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 6. Attach Single Trigger
CREATE TRIGGER on_order_created_steps_v5
    AFTER INSERT ON public.orders
    FOR EACH ROW EXECUTE PROCEDURE public.create_order_steps_safe();

COMMIT;
