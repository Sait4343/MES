-- ==========================================
-- 🛠️ FULL MES SETUP: Quality & Maintenance
-- ==========================================

BEGIN;

-- 1. QUALITY LOGS TABLE (Defects)
-- Tracks non-conformances (NC) linked to specific operations
CREATE TABLE IF NOT EXISTS public.quality_logs (
    id uuid DEFAULT uuid_generate_v4() PRIMARY KEY,
    order_operation_id uuid REFERENCES public.order_operations(id) ON DELETE CASCADE,
    defect_type text NOT NULL, -- 'Scrap' (Брак), 'Rework' (Допрацювання), 'Observation' (Зауваження)
    quantity integer DEFAULT 1,
    reason text,             -- e.g., "Dimensions off", "Surface scratch"
    logged_at timestamptz DEFAULT now(),
    logged_by uuid REFERENCES public.profiles(id) -- Who reported it
);

-- Enable RLS for Quality
ALTER TABLE public.quality_logs ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Quality logs viewable by all" ON public.quality_logs;
CREATE POLICY "Quality logs viewable by all" ON public.quality_logs FOR SELECT TO authenticated USING (true);
DROP POLICY IF EXISTS "Quality logs insertable by workers" ON public.quality_logs;
CREATE POLICY "Quality logs insertable by workers" ON public.quality_logs FOR INSERT TO authenticated WITH CHECK (true);


-- 2. EQUIPMENT DOWNTIME TABLE (Maintenance)
-- Tracks machine/section downtime events
CREATE TABLE IF NOT EXISTS public.equipment_downtime (
    id uuid DEFAULT uuid_generate_v4() PRIMARY KEY,
    section_id uuid REFERENCES public.sections(id), -- Linking to Section for now (Machine level later)
    reason text,             -- e.g., "Tool breakage", "No power", "Maintenance"
    start_time timestamptz DEFAULT now(),
    end_time timestamptz,    -- NULL means currently down
    status text DEFAULT 'open', -- 'open', 'resolved'
    logged_by uuid REFERENCES public.profiles(id)
);

-- Enable RLS for Downtime
ALTER TABLE public.equipment_downtime ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Downtime viewable by all" ON public.equipment_downtime;
CREATE POLICY "Downtime viewable by all" ON public.equipment_downtime FOR SELECT TO authenticated USING (true);
DROP POLICY IF EXISTS "Downtime managed by all" ON public.equipment_downtime;
CREATE POLICY "Downtime managed by all" ON public.equipment_downtime FOR ALL TO authenticated USING (true);

COMMIT;
