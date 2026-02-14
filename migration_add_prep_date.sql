-- Add preparation_date column to orders table
ALTER TABLE public.orders 
ADD COLUMN IF NOT EXISTS preparation_date date;

-- Add start_date if it doesn't exist (it should, but just in case)
ALTER TABLE public.orders 
ADD COLUMN IF NOT EXISTS start_date date;
