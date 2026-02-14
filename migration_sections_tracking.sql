-- ==========================================
-- 🏭 Sections User Tracking Migration
-- ==========================================

-- 1. Add columns if they don't exist
do $$
begin
    if not exists (select 1 from information_schema.columns where table_name='sections' and column_name='created_by') then
        alter table public.sections add column created_by uuid references public.profiles(id);
    end if;

    if not exists (select 1 from information_schema.columns where table_name='sections' and column_name='updated_by') then
        alter table public.sections add column updated_by uuid references public.profiles(id);
    end if;
end $$;

-- 2. Update existing records?
-- We can't know who created old ones, but we can set to current user if running from code, 
-- or leave null. Null is fine for "System/Legacy".

-- 3. Trigger to auto-update updated_at (optional if not already there)
-- Checked init_project.sql, sections has updated_at but no trigger shown in the visible snippet.
-- Let's ensure a trigger updates updated_at.

create or replace function update_updated_at_column()
returns trigger as $$
begin
    new.updated_at = now();
    return new;
end;
$$ language plpgsql;

drop trigger if exists update_sections_updated_at on public.sections;
create trigger update_sections_updated_at
before update on public.sections
for each row execute procedure update_updated_at_column();
