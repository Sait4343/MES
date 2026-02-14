-- Add created_by and updated_by to operations_catalog

BEGIN;

-- 1. Add Columns
ALTER TABLE public.operations_catalog 
ADD COLUMN IF NOT EXISTS created_by uuid REFERENCES public.profiles(id),
ADD COLUMN IF NOT EXISTS updated_by uuid REFERENCES public.profiles(id);

-- 2. Create Indexes for performance
CREATE INDEX IF NOT EXISTS idx_ops_created_by ON public.operations_catalog(created_by);
CREATE INDEX IF NOT EXISTS idx_ops_updated_by ON public.operations_catalog(updated_by);

COMMIT;
