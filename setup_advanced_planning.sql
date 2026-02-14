-- ==========================================
-- 🚀 SETUP ADVANCED PLANNING SCHEMA (Robust Version)
-- ==========================================

BEGIN;

-- 1. SECTIONS TABLE (Дільниці)
create table if not exists public.sections (
    id uuid default uuid_generate_v4() primary key,
    name text not null unique,
    operation_types text[], 
    capacity_minutes numeric default 480, 
    description text,
    created_at timestamptz default now()
);

alter table public.sections enable row level security;
drop policy if exists "Sections viewable by everyone" on public.sections;
create policy "Sections viewable by everyone" on public.sections for select using (true);

drop policy if exists "Sections manageable by Admin/Manager" on public.sections;
create policy "Sections manageable by Admin/Manager" on public.sections for all
using (exists (select 1 from public.profiles where id = auth.uid() and role in ('admin', 'manager')));


-- 2. OPERATIONS CATALOG (Довідник операцій)
create table if not exists public.operations_catalog (
  id uuid default uuid_generate_v4() primary key,
  operation_key text,  
  article text,        
  operation_number text, 
  section text,        
  norm_time numeric default 0, 
  comment text,
  created_at timestamptz default now()
);

alter table public.operations_catalog enable row level security;
drop policy if exists "Operations viewable by everyone" on operations_catalog;
create policy "Operations viewable by everyone" on operations_catalog for select using (true);

drop policy if exists "Operations manageable by Admin/Manager" on operations_catalog;
create policy "Operations manageable by Admin/Manager" on operations_catalog for all
using (exists (select 1 from profiles where id = auth.uid() and role in ('admin', 'manager')));


-- 3. ORDER OPERATIONS (Детальний план замовлення)
create table if not exists public.order_operations (
    id uuid default uuid_generate_v4() primary key,
    order_id uuid references public.orders(id) on delete cascade not null,
    operation_catalog_id uuid references public.operations_catalog(id),
    section_id uuid references public.sections(id),
    assigned_worker_id uuid references public.profiles(id),
    operation_name text, 
    quantity integer default 0,
    norm_time_per_unit numeric default 0, 
    -- total_estimated_time is generated, handled below
    scheduled_start_at timestamptz,
    scheduled_end_at timestamptz,
    status step_status default 'not_started',
    sort_order integer default 0,
    created_at timestamptz default now()
);

-- 3b. ENSURE COLUMNS EXIST (If table existed before)
-- This fixes the "column does not exist" error for indexes
alter table public.order_operations add column if not exists scheduled_start_at timestamptz;
alter table public.order_operations add column if not exists scheduled_end_at timestamptz;
alter table public.order_operations add column if not exists operation_name text;
alter table public.order_operations add column if not exists section_id uuid references public.sections(id);
alter table public.order_operations add column if not exists assigned_worker_id uuid references public.profiles(id);

-- 3c. Generated Column Check (Complex to allow if not exists, skipping for now as it's optimization)

alter table public.order_operations enable row level security;
drop policy if exists "Order Ops viewable by everyone" on public.order_operations;
create policy "Order Ops viewable by everyone" on public.order_operations for select using (true);

drop policy if exists "Order Ops manageable by Admin/Manager" on public.order_operations;
create policy "Order Ops manageable by Admin/Manager" on public.order_operations for all
using (exists (select 1 from public.profiles where id = auth.uid() and role in ('admin', 'manager')));

drop policy if exists "Workers can update their ops" on public.order_operations;
create policy "Workers can update their ops" on public.order_operations for update
using (auth.uid() = assigned_worker_id);

-- Indexes for Charts & Filtering
create index if not exists idx_order_ops_order on order_operations(order_id);
create index if not exists idx_order_ops_worker on order_operations(assigned_worker_id);
-- This validation ensures the column exists before indexing
create index if not exists idx_order_ops_schedule on order_operations(scheduled_start_at, scheduled_end_at);

COMMIT;
