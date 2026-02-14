-- Add preparation_date column to orders table
alter table public.orders 
add column if not exists preparation_date date;
