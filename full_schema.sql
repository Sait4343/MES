-- ==========================================
-- 🏭 Production Planning System - Full Schema
-- ==========================================

-- 1. Extensions & Types
create extension if not exists "uuid-ossp";

do $$ begin
    create type user_role as enum ('admin', 'manager', 'worker');
exception
    when duplicate_object then null;
end $$;

do $$ begin
    create type step_status as enum ('not_started', 'in_progress', 'done', 'problem');
exception
    when duplicate_object then null;
end $$;

-- 2. Profiles (Users & Workers)
create table if not exists public.profiles (
  id uuid references auth.users not null primary key,
  email text,
  full_name text,
  role user_role default 'worker',
  created_at timestamptz default now()
);

alter table public.profiles enable row level security;

create policy "Profiles viewable by everyone" 
  on profiles for select using (true);

create policy "Admins can update all profiles"
  on profiles for update
  using (
    exists (select 1 from profiles where id = auth.uid() and role = 'admin')
  );

-- 3. Orders
create table if not exists public.orders (
  id uuid default uuid_generate_v4() primary key,
  order_number text unique not null,
  product_name text not null,
  article text,
  quantity integer not null default 1,
  contractor text,
  start_date date,
  shipping_date date,
  comment text,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

alter table public.orders enable row level security;

create policy "Orders viewable by everyone" 
  on orders for select using (true);

create policy "Orders manageable by Admin/Manager" 
  on orders for all
  using (
    exists (select 1 from profiles where id = auth.uid() and role in ('admin', 'manager'))
  );

-- 4. Production Steps
create table if not exists public.production_steps (
  id uuid default uuid_generate_v4() primary key,
  order_id uuid references public.orders(id) on delete cascade not null,
  step_name text not null,
  status step_status default 'not_started',
  assigned_worker_id uuid references public.profiles(id),
  started_at timestamptz,
  completed_at timestamptz,
  updated_at timestamptz default now(),
  constraint unique_order_step unique (order_id, step_name)
);

alter table public.production_steps enable row level security;

create policy "Steps viewable by everyone" 
  on production_steps for select using (true);

create policy "Workers notify progress" 
  on production_steps for update
  using (
    -- Worker assigned OR Admin/Manager
    (auth.uid() = assigned_worker_id) or
    exists (select 1 from profiles where id = auth.uid() and role in ('admin', 'manager'))
  );

-- 5. Inventory (Materials)
create table if not exists public.inventory (
  id uuid default uuid_generate_v4() primary key,
  item_name text not null,
  material_type text, -- e.g. 'fabric', 'thread'
  quantity numeric not null default 0,
  unit text not null default 'pcs',
  min_threshold numeric default 10,
  updated_at timestamptz default now()
);

alter table public.inventory enable row level security;

create policy "Inventory viewable by everyone" 
  on inventory for select using (true);

create policy "Inventory manageable by Admin/Manager" 
  on inventory for all
  using (
    exists (select 1 from profiles where id = auth.uid() and role in ('admin', 'manager'))
  );

-- 6. Logs (System Audit)
create table if not exists public.system_logs (
  id uuid default uuid_generate_v4() primary key,
  user_id uuid references public.profiles(id),
  action text not null,
  entity_table text,
  entity_id uuid,
  details jsonb,
  created_at timestamptz default now()
);

alter table public.system_logs enable row level security;

create policy "Logs viewable by Admin" 
  on system_logs for select
  using (
    exists (select 1 from profiles where id = auth.uid() and role = 'admin')
  );

create policy "System can create logs"
  on system_logs for insert
  with check (auth.uid() = user_id);

-- 7. Indexes
create index if not exists idx_orders_number on orders(order_number);
create index if not exists idx_steps_order on production_steps(order_id);
create index if not exists idx_logs_created on system_logs(created_at desc);

-- 8. Triggers (Sync Profiles)
create or replace function public.handle_new_user()
returns trigger as $$
begin
  insert into public.profiles (id, email, full_name, role)
  values (new.id, new.email, new.raw_user_meta_data->>'full_name', 'worker')
  on conflict (id) do nothing;
  return new;
end;
$$ language plpgsql security definer;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute procedure public.handle_new_user();

-- Trigger for Auto-Steps (Simplified)
create or replace function create_default_steps()
returns trigger as $$
declare
  steps text[] := array['cutting', 'basting', 'sewing', 'overlock', 'completing', 'edging', 'finishing', 'fixing', 'packing'];
  s text;
begin
  foreach s in array steps
  loop
    insert into public.production_steps (order_id, step_name)
    values (new.id, s)
    on conflict do nothing;
  end loop;
  return new;
end;
$$ language plpgsql;

drop trigger if exists on_order_created_steps on public.orders;
create trigger on_order_created_steps
  after insert on public.orders
  for each row execute procedure create_default_steps();
