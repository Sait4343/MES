-- =========================================================
-- 🛠️ COMPREHENSIVE FIX: Order Creation & Step Name Type
-- =========================================================

-- We wrap this in a transaction block to ensure atomicity
BEGIN;

-- 1. 🧹 CLEANUP: Remove old triggers and functions
DROP TRIGGER IF EXISTS on_order_created_steps ON public.orders;
DROP FUNCTION IF EXISTS public.create_default_steps();
DROP FUNCTION IF EXISTS public.create_order_steps_text();

-- 2. 🧹 CLEANUP: Remove Type (if exists) and handle dependencies
-- We accept that this might fail if used by other things, so we try specific cleanup first.
-- Dropping the unique constraint first because it depends on the column
ALTER TABLE public.production_steps DROP CONSTRAINT IF EXISTS unique_order_step;

-- 3. 🔧 MODIFY TABLE: Force step_name to TEXT
-- This is the critical step. We want to ensure it is standard TEXT.
ALTER TABLE public.production_steps 
ALTER COLUMN step_name TYPE text USING step_name::text;

-- 4. 🔗 RESTORE: Re-add Constraints
ALTER TABLE public.production_steps 
ADD CONSTRAINT unique_order_step UNIQUE (order_id, step_name);

-- 5. 🗑️ DROP TYPE: Now we can safely drop the custom type "step_name"
-- We use IF EXISTS to avoid errors if it's already gone.
DROP TYPE IF EXISTS public.step_name;

-- 6. ✨ RECREATE LOGIC: New Function and Trigger
CREATE OR REPLACE FUNCTION public.create_order_steps_final()
RETURNS trigger AS $$
DECLARE
    -- Explicitly Text Array
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

CREATE TRIGGER on_order_created_steps
    AFTER INSERT ON public.orders
    FOR EACH ROW EXECUTE PROCEDURE public.create_order_steps_final();

COMMIT;
