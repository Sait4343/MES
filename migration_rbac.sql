-- ==========================================
-- 🛡️ RBAC Migration Script
-- ==========================================

-- 1. Add 'viewer' role to enum
-- Note: This command cannot run inside a transaction block in some postgres versions/tools. 
-- If it fails, run it separately: ALTER TYPE user_role ADD VALUE IF NOT EXISTS 'viewer';
ALTER TYPE user_role ADD VALUE IF NOT EXISTS 'viewer';

-- 2. Update Profiles Policies
drop policy if exists "Profiles viewable by everyone" on profiles;
drop policy if exists "Admins can update all profiles" on profiles;

create policy "Profiles viewable by everyone" 
  on profiles for select using (true);

create policy "Admins can update all profiles"
  on profiles for update
  using (
    exists (select 1 from profiles where id = auth.uid() and role = 'admin')
  );

-- 3. Update Orders Policies
drop policy if exists "Orders viewable by everyone" on orders;
drop policy if exists "Orders manageable by Admin/Manager" on orders;

create policy "Orders viewable by everyone (Read)" 
  on orders for select using (true);

create policy "Orders manageable by Admin/Manager (Write)" 
  on orders for all
  using (
    exists (select 1 from profiles where id = auth.uid() and role in ('admin', 'manager'))
  );

-- 4. Update Production Steps Policies
drop policy if exists "Steps viewable by everyone" on production_steps;
drop policy if exists "Workers notify progress" on production_steps;

create policy "Steps viewable by everyone (Read)" 
  on production_steps for select using (true);

create policy "Steps updateable by Admin/Manager/Worker" 
  on production_steps for update
  using (
    exists (select 1 from profiles where id = auth.uid() and role in ('admin', 'manager', 'worker'))
  );
  
-- Note: Insert/Delete steps is restricted to Admin/Manager typically via the Order Management, 
-- but if Workers need to create steps? Usually no.
create policy "Steps insert/delete by Admin/Manager"
  on production_steps for insert
  with check (
    exists (select 1 from profiles where id = auth.uid() and role in ('admin', 'manager'))
  );
  
create policy "Steps delete by Admin/Manager"
  on production_steps for delete
  using (
    exists (select 1 from profiles where id = auth.uid() and role in ('admin', 'manager'))
  );


-- 5. Update Inventory Policies
drop policy if exists "Inventory viewable by everyone" on inventory;
drop policy if exists "Inventory manageable by Admin/Manager" on inventory;

create policy "Inventory viewable by everyone (Read)" 
  on inventory for select using (true);

create policy "Inventory manageable by Admin/Manager (Write)" 
  on inventory for all
  using (
    exists (select 1 from profiles where id = auth.uid() and role in ('admin', 'manager'))
  );

-- 6. System Logs
-- Admin only read access already established, validating.
drop policy if exists "Logs viewable by Admin" on system_logs;
create policy "Logs viewable by Admin" 
  on system_logs for select
  using (
    exists (select 1 from profiles where id = auth.uid() and role = 'admin')
  );
