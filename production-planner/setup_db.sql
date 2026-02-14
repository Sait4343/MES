-- Enable necessary extensions
create extension if not exists "uuid-ossp";

-- Define Enums
create type user_role as enum ('admin', 'manager', 'worker');
create type step_status as enum ('not_started', 'in_progress', 'done', 'problem');
create type step_name as enum (
  'cutting',
  'basting',
  'completing',
  'overlock',
  'sewing',
  'edging',
  'finishing',
  'fixing',
  'packing'
);

-- Profiles Table (Users)
create table public.profiles (
  id uuid references auth.users not null primary key,
  email text,
  full_name text,
  role user_role default 'worker',
  created_at timestamptz default now()
);

-- Enable RLS for Profiles
alter table public.profiles enable row level security;

create policy "Public profiles are viewable by everyone."
  on profiles for select
  using ( true );

create policy "Users can update own profile."
  on profiles for update
  using ( auth.uid() = id );

-- Orders Table
create table public.orders (
  id uuid default uuid_generate_v4() primary key,
  order_number text unique not null,
  product_name text not null,
  article text,
  quantity integer not null default 1,
  version text,
  contractor text,
  start_date date,
  shipping_date date,
  comment text,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

-- Enable RLS for Orders
alter table public.orders enable row level security;

create policy "Orders are viewable by everyone."
  on orders for select
  using ( true );

create policy "Only Admins and Managers can insert orders."
  on orders for insert
  with check (
    exists (
      select 1 from profiles
      where profiles.id = auth.uid()
      and role in ('admin', 'manager')
    )
  );

create policy "Only Admins and Managers can update orders."
  on orders for update
  using (
    exists (
      select 1 from profiles
      where profiles.id = auth.uid()
      and role in ('admin', 'manager')
    )
  );
  
create policy "Only Admins can delete orders."
  on orders for delete
  using (
    exists (
      select 1 from profiles
      where profiles.id = auth.uid()
      and role = 'admin'
    )
  );

-- Production Steps Table
create table public.production_steps (
  id uuid default uuid_generate_v4() primary key,
  order_id uuid references public.orders(id) on delete cascade not null,
  step_name step_name not null,
  status step_status default 'not_started',
  assigned_worker_id uuid references public.profiles(id),
  started_at timestamptz,
  completed_at timestamptz,
  updated_at timestamptz default now(),
  constraint unique_order_step unique (order_id, step_name)
);

-- Enable RLS for Production Steps
alter table public.production_steps enable row level security;

create policy "Production steps are viewable by everyone."
  on production_steps for select
  using ( true );

create policy "Workers can update their assigned steps."
  on production_steps for update
  using (
    (auth.uid() = assigned_worker_id) or
    exists (
      select 1 from profiles
      where profiles.id = auth.uid()
      and role in ('admin', 'manager')
    )
  );

-- Function to handle new user signup
create or replace function public.handle_new_user()
returns trigger as $$
begin
  insert into public.profiles (id, email, full_name, role)
  values (new.id, new.email, new.raw_user_meta_data->>'full_name', 'worker');
  return new;
end;
$$ language plpgsql security definer;

-- Trigger to call handle_new_user on signup
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute procedure public.handle_new_user();

-- Function to update updated_at timestamp
create or replace function update_updated_at_column()
returns trigger as $$
begin
    new.updated_at = now();
    return new;
end;
$$ language plpgsql;

-- Trigger for Orders
create trigger update_orders_updated_at
    before update on public.orders
    for each row execute procedure update_updated_at_column();

-- Trigger for Production Steps
create trigger update_production_steps_updated_at
    before update on public.production_steps
    for each row execute procedure update_updated_at_column();

-- Function to auto-create production steps when an order is created
create or replace function create_production_steps()
returns trigger as $$
declare
  s step_name;
begin
  foreach s in array enum_range(null::step_name)
  loop
    insert into public.production_steps (order_id, step_name)
    values (new.id, s);
  end loop;
  return new;
end;
$$ language plpgsql;

create trigger on_order_created
  after insert on public.orders
  for each row execute procedure create_production_steps();
