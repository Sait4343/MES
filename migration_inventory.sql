-- Inventory Table
create table public.inventory (
  id uuid default uuid_generate_v4() primary key,
  item_name text not null,
  quantity numeric not null default 0,
  unit text not null default 'pcs',
  min_threshold numeric default 10,
  updated_at timestamptz default now()
);

-- RLS for Inventory
alter table public.inventory enable row level security;

create policy "Inventory viewable by everyone"
  on inventory for select using (true);

create policy "Inventory manageable by Admin/Manager"
  on inventory for all
  using (
    exists (
      select 1 from profiles
      where profiles.id = auth.uid()
      and role in ('admin', 'manager')
    )
  );
