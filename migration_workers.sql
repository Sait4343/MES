-- Allow Admins to update any profile (e.g. to change roles)
create policy "Admins can update all profiles"
  on public.profiles
  for update
  using (
    exists (
      select 1 from profiles
      where profiles.id = auth.uid()
      and role = 'admin'
    )
  );
