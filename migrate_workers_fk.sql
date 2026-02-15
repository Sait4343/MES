-- ==========================================
-- 🛠️ WORKERS TABLE MIGRATION & FK UPDATE
-- ==========================================

BEGIN;

-- 1. Ensure `workers` table exists (and copy from profiles if empty)
-- (Simplified version of migration_separate_workers.sql)
CREATE TABLE IF NOT EXISTS public.workers (
    id uuid DEFAULT uuid_generate_v4() PRIMARY KEY,
    full_name text NOT NULL,
    position text,
    competence text,
    comment text,
    operation_types text[],
    section_id uuid REFERENCES public.sections(id), -- Added section_id
    created_at timestamptz DEFAULT now(),
    updated_at timestamptz DEFAULT now()
);

-- 2. Populate 'workers' if empty (from profiles usually)
INSERT INTO public.workers (full_name, position, operation_types)
SELECT full_name, role, operation_types 
FROM public.profiles 
WHERE role = 'worker'
AND NOT EXISTS (SELECT 1 FROM public.workers);

-- 3. Auto-link workers to sections based on operation_types (Best Effort)
UPDATE public.workers w
SET section_id = s.id
FROM public.sections s
WHERE w.section_id IS NULL 
AND s.name = ANY(w.operation_types);

-- 4. UPDATE foreign key in `order_operations`
-- CAUTION: This drops the constraint to profiles. 
-- Existing IDs in assigned_worker_id might be invalid if they refer to profiles.
ALTER TABLE public.order_operations 
DROP CONSTRAINT IF EXISTS order_operations_assigned_worker_id_fkey;

ALTER TABLE public.order_operations 
ADD CONSTRAINT order_operations_assigned_worker_id_fkey 
FOREIGN KEY (assigned_worker_id) REFERENCES public.workers(id);

-- Enable RLS for workers
ALTER TABLE public.workers ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Workers viewable by authenticated" ON public.workers;
CREATE POLICY "Workers viewable by authenticated" ON public.workers FOR SELECT TO authenticated USING (true);

COMMIT;
