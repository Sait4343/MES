-- ==========================================
-- 🧨 Force Fix: Column Swap Strategy
-- ==========================================

BEGIN;

-- 1. Disarm Triggers
DROP TRIGGER IF EXISTS on_order_created_steps ON public.orders;

-- 2. Swap Column Logic (Bypass "Type" issues)
-- A. Add new TEXT column
ALTER TABLE public.production_steps ADD COLUMN IF NOT EXISTS step_name_new TEXT;

-- B. Copy data (Cast existing enum/text to text)
UPDATE public.production_steps SET step_name_new = step_name::text;

-- C. Drop constraints on old column
ALTER TABLE public.production_steps DROP CONSTRAINT IF EXISTS unique_order_step;

-- D. Drop OLD column (This kills the dependency on the missing type)
ALTER TABLE public.production_steps DROP COLUMN step_name CASCADE;

-- E. Rename NEW column
ALTER TABLE public.production_steps RENAME COLUMN step_name_new TO step_name;

-- F. Restore Constraint
ALTER TABLE public.production_steps ADD CONSTRAINT unique_order_step UNIQUE (order_id, step_name);

-- 3. Cleanup Old Type (Just in case)
DROP TYPE IF EXISTS public.step_name;

-- 4. Recreate Function & Trigger (Version 4)
CREATE OR REPLACE FUNCTION public.create_order_steps_v4()
RETURNS trigger AS $$
DECLARE
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
    FOR EACH ROW EXECUTE PROCEDURE public.create_order_steps_v4();

COMMIT;
