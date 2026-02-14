-- ==========================================
-- 🛠️ Fix: Create missing system_logs table
-- ==========================================

-- 1. Create table
create table if not exists public.system_logs (
  id uuid default uuid_generate_v4() primary key,
  user_id uuid references public.profiles(id),
  action text not null,
  entity_table text,
  entity_id uuid,
  details jsonb,
  created_at timestamptz default now()
);

-- 2. Enable RLS
alter table public.system_logs enable row level security;

-- 3. Create/Update Policies
drop policy if exists "Logs viewable by Admin" on system_logs;

create policy "Logs viewable by Admin" 
  on system_logs for select
  using (
    exists (select 1 from profiles where id = auth.uid() and role = 'admin')
  );

drop policy if exists "System can create logs" on system_logs;

create policy "System can create logs"
  on system_logs for insert
  with check (auth.uid() = user_id);

-- 4. Create Index
create index if not exists idx_logs_created on system_logs(created_at desc);
