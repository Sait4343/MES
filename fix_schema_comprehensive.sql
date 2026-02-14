-- Comprehensive Fix for "step_name" type error
-- This script safely removes the dependency on the Enum type and ensures everything is TEXT.

BEGIN;

-- 1. Drop existing Trigger and Function to clear compiled plans
DROP TRIGGER IF EXISTS on_order_created_steps ON public.orders;
DROP FUNCTION IF EXISTS public.create_default_steps();

-- 2. Force column to TEXT
-- If it's already text, this is a no-op.
-- If it was an enum, we cast it. If the type is missing, we try to just set it to text.
ALTER TABLE public.production_steps 
ALTER COLUMN step_name TYPE text USING step_name::text;

-- 3. Drop the enum type if it still exists (it might be causing issues if referenced elsewhere)
DROP TYPE IF EXISTS step_name;

-- 4. Re-create the function (Explicitly using TEXT)
CREATE OR REPLACE FUNCTION public.create_default_steps()
RETURNS TRIGGER AS $$
DECLARE
  -- Define steps as array of TEXT
  steps text[] := array['cutting', 'basting', 'sewing', 'overlock', 'completing', 'edging', 'finishing', 'fixing', 'packing'];
  s text;
BEGIN
  FOREACH s IN ARRAY steps
  LOOP
    INSERT INTO public.production_steps (order_id, step_name)
    VALUES (new.id, s)
    ON CONFLICT DO NOTHING;
  END LOOP;
  RETURN new;
END;
$$ LANGUAGE plpgsql;

-- 5. Re-create the trigger
CREATE TRIGGER on_order_created_steps
  AFTER INSERT ON public.orders
  FOR EACH ROW EXECUTE PROCEDURE public.create_default_steps();

COMMIT;
