-- Fix for Error: column "step_name" is of type step_name but expression is of type text
-- This alters the column to be generic TEXT, allowing any operation name.

BEGIN;

-- 1. Alter the column type to TEXT
ALTER TABLE public.production_steps 
ALTER COLUMN step_name TYPE text USING step_name::text;

-- 2. (Optional) Drop the enum type if it exists and is no longer needed
DROP TYPE IF EXISTS step_name;

COMMIT;
