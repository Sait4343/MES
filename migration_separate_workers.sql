-- ==========================================
-- 🏭 Separate Workers Table Migration
-- ==========================================

-- 1. Create the `workers` table
create table if not exists public.workers (
    id uuid default uuid_generate_v4() primary key,
    full_name text not null,
    position text,
    competence text,
    comment text,
    operation_types text[], -- Array of strings
    
    -- Tracking
    created_at timestamptz default now(),
    updated_at timestamptz default now(),
    created_by uuid references public.profiles(id),
    updated_by uuid references public.profiles(id)
);

-- 2. Enable RLS
alter table public.workers enable row level security;

-- 3. Policies (Allow full access to authenticated users for now)
create policy "Enable read access for authenticated users"
on public.workers for select
to authenticated
using (true);

create policy "Enable insert for authenticated users"
on public.workers for insert
to authenticated
with check (true);

create policy "Enable update for authenticated users"
on public.workers for update
to authenticated
using (true);

create policy "Enable delete for authenticated users"
on public.workers for delete
to authenticated
using (true);

-- 4. Auto-update `updated_at` trigger
-- Create the function if it doesn't exist
create or replace function public.update_updated_at_column()
returns trigger as $$
begin
    new.updated_at = now();
    return new;
end;
$$ language plpgsql;

create trigger handle_updated_at before update on public.workers
for each row execute procedure public.update_updated_at_column();

-- 5. Data Migration: Copy existing 'workers' from profiles
insert into public.workers (
    full_name, 
    position, 
    competence, 
    comment, 
    operation_types, 
    created_at, 
    updated_at, 
    created_by, 
    updated_by
)
select 
    full_name, 
    position, 
    competence, 
    comment, 
    operation_types, 
    created_at, 
    updated_at, 
    created_by, 
    updated_by
from public.profiles
where role = 'worker';

-- Optional: You might want to delete them from profiles later, 
-- but for safety we keep them there for now (or user manually deletes).
