-- ==========================================
-- 🏭 Production Planning System - Init Script
-- ==========================================
-- Run this script in Supabase SQL Editor to initialize the database.
-- It handles Types, Tables, Triggers, and RLS Policies.

-- 1. Extensions
create extension if not exists "uuid-ossp";

-- 2. Enums
do $$ begin
    create type user_role as enum ('admin', 'manager', 'worker', 'viewer');
exception
    when duplicate_object then null;
end $$;

do $$ begin
    create type step_status as enum ('not_started', 'in_progress', 'done', 'problem');
exception
    when duplicate_object then null;
end $$;

-- 3. Profiles
create table if not exists public.profiles (
  id uuid references auth.users not null primary key,
  email text,
  full_name text,
  role user_role default 'worker',
  created_at timestamptz default now()
);

alter table public.profiles enable row level security;

-- Profiles Policies
drop policy if exists "Profiles viewable by everyone" on profiles;
create policy "Profiles viewable by everyone" on profiles for select using (true);

drop policy if exists "Admins can update all profiles" on profiles;
create policy "Admins can update all profiles" on profiles for update
  using (exists (select 1 from profiles where id = auth.uid() and role = 'admin'));

-- 4. Orders
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

-- Orders Policies
drop policy if exists "Orders viewable by everyone" on orders; 
drop policy if exists "Orders viewable by everyone (Read)" on orders; -- Clean up new name too
create policy "Orders viewable by everyone (Read)" on orders for select using (true);

drop policy if exists "Orders manageable by Admin/Manager" on orders;
drop policy if exists "Orders manageable by Admin/Manager (Write)" on orders;
create policy "Orders manageable by Admin/Manager (Write)" on orders for all
  using (exists (select 1 from profiles where id = auth.uid() and role in ('admin', 'manager')));

-- 5. Production Steps
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

-- Steps Policies
drop policy if exists "Steps viewable by everyone" on production_steps;
drop policy if exists "Steps viewable by everyone (Read)" on production_steps;
create policy "Steps viewable by everyone (Read)" on production_steps for select using (true);

drop policy if exists "Workers notify progress" on production_steps;
drop policy if exists "Steps updateable by Admin/Manager/Worker" on production_steps;
create policy "Steps updateable by Admin/Manager/Worker" on production_steps for update
  using (exists (select 1 from profiles where id = auth.uid() and role in ('admin', 'manager', 'worker')));

drop policy if exists "Steps insert/delete by Admin/Manager" on production_steps;
create policy "Steps insert/delete by Admin/Manager" on production_steps for insert
  with check (exists (select 1 from profiles where id = auth.uid() and role in ('admin', 'manager')));

drop policy if exists "Steps delete by Admin/Manager" on production_steps;
create policy "Steps delete by Admin/Manager" on production_steps for delete
  using (exists (select 1 from profiles where id = auth.uid() and role in ('admin', 'manager')));

-- 6. Inventory
create table if not exists public.inventory (
  id uuid default uuid_generate_v4() primary key,
  item_name text not null,
  material_type text, 
  quantity numeric not null default 0,
  unit text not null default 'pcs',
  min_threshold numeric default 10,
  updated_at timestamptz default now()
);

alter table public.inventory enable row level security;

-- Inventory Policies
drop policy if exists "Inventory viewable by everyone" on inventory;
drop policy if exists "Inventory viewable by everyone (Read)" on inventory;
create policy "Inventory viewable by everyone (Read)" on inventory for select using (true);

drop policy if exists "Inventory manageable by Admin/Manager" on inventory;
drop policy if exists "Inventory manageable by Admin/Manager (Write)" on inventory;
create policy "Inventory manageable by Admin/Manager (Write)" on inventory for all
  using (exists (select 1 from profiles where id = auth.uid() and role in ('admin', 'manager')));

-- 7. System Logs (Audit)
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

-- Logs Policies
drop policy if exists "Logs viewable by Admin" on system_logs;
create policy "Logs viewable by Admin" on system_logs for select
  using (exists (select 1 from profiles where id = auth.uid() and role = 'admin'));

drop policy if exists "System can create logs" on system_logs;
create policy "System can create logs" on system_logs for insert
  with check (auth.uid() = user_id);

-- 8. Indexes
create index if not exists idx_orders_number on orders(order_number);
create index if not exists idx_steps_order on production_steps(order_id);
create index if not exists idx_logs_created on system_logs(created_at desc);

-- 9. Triggers
-- Handle New User (Profile Creation)
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

-- Auto-Create Steps for New Orders
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
