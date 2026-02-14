-- ==========================================
-- 🧵 Operations Catalog Migration
-- ==========================================

-- 1. Create Table
create table if not exists public.operations_catalog (
  id uuid default uuid_generate_v4() primary key,
  operation_key text,  -- Ключ операції
  article text,        -- Артикул
  operation_number text, -- № операції
  section text,        -- Дільниця
  norm_time numeric default 0, -- Норма, хв
  comment text,        -- Коментар
  -- Optional based on common textile needs, though not strictly in text list but in screenshot:
  color text,          
  
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

-- 2. Enable RLS
alter table public.operations_catalog enable row level security;

-- 3. Policies
-- Everyone can read
drop policy if exists "Operations viewable by everyone" on operations_catalog;
create policy "Operations viewable by everyone" 
  on operations_catalog for select using (true);

-- Only Admin/Manager can edit
drop policy if exists "Operations manageable by Admin/Manager" on operations_catalog;
create policy "Operations manageable by Admin/Manager" 
  on operations_catalog for all
  using (
    exists (select 1 from profiles where id = auth.uid() and role in ('admin', 'manager'))
  );

-- 4. Indexes
create index if not exists idx_ops_article on operations_catalog(article);
create index if not exists idx_ops_key on operations_catalog(operation_key);
