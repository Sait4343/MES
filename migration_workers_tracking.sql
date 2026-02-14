-- ==========================================
-- 👥 Workers (Profiles) Tracking Migration
-- ==========================================

-- 1. Add columns if they don't exist
do $$
begin
    if not exists (select 1 from information_schema.columns where table_name='profiles' and column_name='created_by') then
        alter table public.profiles add column created_by uuid references public.profiles(id);
    end if;

    if not exists (select 1 from information_schema.columns where table_name='profiles' and column_name='updated_by') then
        alter table public.profiles add column updated_by uuid references public.profiles(id);
    end if;
    
    if not exists (select 1 from information_schema.columns where table_name='profiles' and column_name='comment') then
        alter table public.profiles add column comment text;
    end if;
    
    if not exists (select 1 from information_schema.columns where table_name='profiles' and column_name='updated_at') then
        alter table public.profiles add column updated_at timestamptz default now();
    end if;
end $$;

-- 2. Trigger to auto-update updated_at for profiles
create or replace function update_profiles_updated_at()
returns trigger as $$
begin
    new.updated_at = now();
    return new;
end;
$$ language plpgsql;

drop trigger if exists update_profiles_updated_at_trigger on public.profiles;
create trigger update_profiles_updated_at_trigger
before update on public.profiles
for each row execute procedure update_profiles_updated_at();
