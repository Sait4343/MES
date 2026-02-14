-- Advanced Planning Schema

-- 1. Table: Order Operations (The text-based 'production_steps' table will eventually be superseded by this or linked)
-- We keep 'production_steps' for the simple view, but 'order_operations' allows detailed mapping to the Catalog.

create table if not exists public.order_operations (
    id uuid default uuid_generate_v4() primary key,
    order_id uuid references public.orders(id) on delete cascade not null,
    operation_catalog_id uuid references public.operations_catalog(id), -- Link to source definition
    section_id uuid references public.sections(id), -- Assigned section
    assigned_worker_id uuid references public.profiles(id), -- Assigned worker
    
    -- Snapshots & Estimates
    operation_name text, -- Snapshot name in case catalog detailed changes
    quantity integer default 0,
    norm_time_per_unit numeric default 0, -- Minutes
    total_estimated_time numeric generated always as (quantity * norm_time_per_unit) stored, -- Minutes
    
    -- Scheduling
    planned_date date,
    sort_order integer default 0,
    status step_status default 'not_started',
    
    created_at timestamptz default now(),
    updated_at timestamptz default now()
);

-- 2. RLS
alter table public.order_operations enable row level security;

create policy "Order Ops viewable by everyone" on public.order_operations for select using (true);

create policy "Order Ops manageable by Admin/Manager" on public.order_operations for all
using (exists (select 1 from public.profiles where id = auth.uid() and role in ('admin', 'manager')));

create policy "Workers can update their ops" on public.order_operations for update
using (auth.uid() = assigned_worker_id);

-- 3. Indexes
create index if not exists idx_order_ops_order on order_operations(order_id);
create index if not exists idx_order_ops_worker on order_operations(assigned_worker_id);
create index if not exists idx_order_ops_date on order_operations(planned_date);
