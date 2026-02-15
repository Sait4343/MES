-- Add section_id to profiles for strict assignment
ALTER TABLE public.profiles 
ADD COLUMN IF NOT EXISTS section_id uuid REFERENCES public.sections(id);

-- Optional: Create index
CREATE INDEX IF NOT EXISTS idx_profiles_section ON public.profiles(section_id);

-- Migration Helper: If profiles have 'operation_types' array containing section name, 
-- try to map it to section_id (if exact name match exists)
-- This is a best-effort auto-link for existing users
DO $$
BEGIN
    UPDATE public.profiles p
    SET section_id = s.id
    FROM public.sections s
    WHERE p.section_id IS NULL 
    AND s.name = ANY(p.operation_types);
END $$;
