-- ==========================================
-- 🛠️ FIX WORKERS RELATIONSHIP & DATA (ROBUST)
-- ==========================================

BEGIN;

-- 1. Ensure `workers` table exists
CREATE TABLE IF NOT EXISTS public.workers (
    id uuid DEFAULT uuid_generate_v4() PRIMARY KEY,
    full_name text NOT NULL,
    position text,
    competence text,
    comment text,
    operation_types text[],
    section_id uuid REFERENCES public.sections(id),
    created_by uuid REFERENCES public.profiles(id),
    updated_by uuid REFERENCES public.profiles(id),
    created_at timestamptz DEFAULT now(),
    updated_at timestamptz DEFAULT now()
);

-- 1b. Add audit columns if they don't exist (for existing tables)
ALTER TABLE public.workers ADD COLUMN IF NOT EXISTS created_by uuid REFERENCES public.profiles(id);
ALTER TABLE public.workers ADD COLUMN IF NOT EXISTS updated_by uuid REFERENCES public.profiles(id);

-- 2. Populate 'workers' from 'profiles' (if not already populated)
-- We use DISTINCT full_name to avoid duplicates if run multiple times
INSERT INTO public.workers (full_name, position, operation_types)
SELECT DISTINCT full_name, role, operation_types 
FROM public.profiles 
WHERE role = 'worker'
AND full_name NOT IN (SELECT full_name FROM public.workers);

-- 3. MIGRATE DATA: Update order_operations to point to new worker IDs
-- We match by Full Name, assuming names are unique enough for this migration
UPDATE public.order_operations oo
SET assigned_worker_id = w.id
FROM public.workers w, public.profiles p
WHERE oo.assigned_worker_id = p.id -- Current ID is a Profile ID
AND p.full_name = w.full_name;     -- Find Worker with same name

-- 4. Clean up unmatched/invalid IDs (Set to NULL to avoid FK violation)
-- If a profile doesn't have a corresponding worker entry, unassign the task
UPDATE public.order_operations
SET assigned_worker_id = NULL
WHERE assigned_worker_id NOT IN (SELECT id FROM public.workers);

-- 5. UPDATE foreign key constraint
-- Drop old constraints (try both names)
ALTER TABLE public.order_operations 
DROP CONSTRAINT IF EXISTS order_operations_assigned_worker_id_fkey;

ALTER TABLE public.order_operations 
DROP CONSTRAINT IF EXISTS order_operations_profile_id_fkey; -- Just in case

-- Add NEW constraint referencing workers
ALTER TABLE public.order_operations 
ADD CONSTRAINT order_operations_assigned_worker_id_fkey 
FOREIGN KEY (assigned_worker_id) REFERENCES public.workers(id);

-- 6. Refresh Schema Cache (Not forced here, but structure change usually triggers it)
NOTIFY pgrst, 'reload schema';

COMMIT;
