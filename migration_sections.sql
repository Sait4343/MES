-- Create Sections Table
create table if not exists public.sections (
    id uuid default uuid_generate_v4() primary key,
    name text not null unique,
    operation_types text[], -- Array of strings (e.g. ['Sewing', 'Cutting'])
    capacity_minutes numeric default 0, -- Time available for this section (per shift/day?)
    description text,
    created_at timestamptz default now(),
    updated_at timestamptz default now()
);

-- Enable RLS
alter table public.sections enable row level security;

-- Policies
create policy "Sections viewable by everyone" on public.sections for select using (true);

create policy "Sections manageable by Admin/Manager" on public.sections for all
using (exists (select 1 from public.profiles where id = auth.uid() and role in ('admin', 'manager')));

-- Note: 'operation_types' here stores the *types* of operations this section can handle.
-- This aligns with user request "types of operations which can be chosen from operations page".
-- We assume these 'types' are the 'section' column values in 'operations_catalog' or a new concept.
-- Given the context, it likely maps to 'section' in operations_catalog.
