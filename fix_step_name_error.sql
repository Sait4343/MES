-- Fix for Error: type "step_name" does not exist
-- 1. Ensure production_steps.step_name is TEXT
-- 2. Redefine create_default_steps function to use TEXT array

BEGIN;

-- 1. Alter Column Type (Safe if already text)
ALTER TABLE public.production_steps 
ALTER COLUMN step_name TYPE text USING step_name::text;

-- 2. Drop the custom type if it exists (Cleaning up)
-- We use a DO block to avoid errors if it doesn't exist or is in use (though we just removed usage in the table)
DO $$ BEGIN
    DROP TYPE IF EXISTS public.step_name;
EXCEPTION
    WHEN OTHERS THEN NULL;
END $$;

-- 3. Redefine Trigger Function to be explicit about types
CREATE OR REPLACE FUNCTION public.create_default_steps()
RETURNS trigger AS $$
DECLARE
  -- Explicitly define as TEXT array
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

COMMIT;
