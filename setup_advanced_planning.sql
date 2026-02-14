-- ==========================================
-- 🚀 SETUP ADVANCED PLANNING SCHEMA
-- ==========================================

BEGIN;

-- 1. SECTIONS TABLE (Дільниці)
-- Represents physical or logical production areas (Cutting, Sewing, etc.)
create table if not exists public.sections (
    id uuid default uuid_generate_v4() primary key,
    name text not null unique,
    operation_types text[], -- Array of strings (e.g. ['Sewing', 'Cutting'])
    capacity_minutes numeric default 480, -- Daily capacity in minutes (8 hours default)
    description text,
    created_at timestamptz default now()
);

alter table public.sections enable row level security;
create policy "Sections viewable by everyone" on public.sections for select using (true);
create policy "Sections manageable by Admin/Manager" on public.sections for all
using (exists (select 1 from public.profiles where id = auth.uid() and role in ('admin', 'manager')));


-- 2. OPERATIONS CATALOG (Довідник операцій)
-- Library of all possible operations with standard times
create table if not exists public.operations_catalog (
  id uuid default uuid_generate_v4() primary key,
  operation_key text,  -- Unique code/key
  article text,        -- Product link
  operation_number text, 
  section text,        -- Section name (text link)
  norm_time numeric default 0, -- Standard time in minutes
  comment text,
  created_at timestamptz default now()
);

alter table public.operations_catalog enable row level security;
create policy "Operations viewable by everyone" on operations_catalog for select using (true);
create policy "Operations manageable by Admin/Manager" on operations_catalog for all
using (exists (select 1 from profiles where id = auth.uid() and role in ('admin', 'manager')));


-- 3. ORDER OPERATIONS (Детальний план замовлення)
-- Specific operations assigned to a specific order, scheduled in time
create table if not exists public.order_operations (
    id uuid default uuid_generate_v4() primary key,
    order_id uuid references public.orders(id) on delete cascade not null,
    
    -- Link to catalog (optional, for reference)
    operation_catalog_id uuid references public.operations_catalog(id),
    
    -- Scheduling Details
    section_id uuid references public.sections(id),
    assigned_worker_id uuid references public.profiles(id),
    
    operation_name text not null, -- Snapshot name
    quantity integer default 0,
    norm_time_per_unit numeric default 0, 
    
    -- Calculated total time (quantity * norm)
    total_estimated_time numeric generated always as (quantity * norm_time_per_unit) stored,
    
    -- Precise Scheduling for Gantt
    scheduled_start_at timestamptz,
    scheduled_end_at timestamptz,
    
    status step_status default 'not_started',
    sort_order integer default 0,
    
    created_at timestamptz default now()
);

alter table public.order_operations enable row level security;
create policy "Order Ops viewable by everyone" on public.order_operations for select using (true);
create policy "Order Ops manageable by Admin/Manager" on public.order_operations for all
using (exists (select 1 from public.profiles where id = auth.uid() and role in ('admin', 'manager')));
create policy "Workers can update their ops" on public.order_operations for update
using (auth.uid() = assigned_worker_id);

-- Indexes for Charts & Filtering
create index if not exists idx_order_ops_order on order_operations(order_id);
create index if not exists idx_order_ops_worker on order_operations(assigned_worker_id);
create index if not exists idx_order_ops_schedule on order_operations(scheduled_start_at, scheduled_end_at);

COMMIT;
