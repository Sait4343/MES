-- Add new columns to profiles table
ALTER TABLE public.profiles 
ADD COLUMN IF NOT EXISTS "position" text,
ADD COLUMN IF NOT EXISTS "competence" text,
ADD COLUMN IF NOT EXISTS "operation_types" text[]; -- Array of strings for multiple operation types

-- Update RLS policies to ensure these columns are accessible
-- Existing policies "Admins can update all profiles" and "Profiles viewable by everyone" should cover this.
-- We might need to ensure 'manager' can also update these fields if requested, but user said "Workers page... import/export" -> implies Manager/Admin.

-- Grant update on these columns specifically if needed, but the row-level update policy covers the whole row.
