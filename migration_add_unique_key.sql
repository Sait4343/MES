-- Add UNIQUE constraint to operation_key to support upsert
-- Note: This might fail if there are already duplicates. 
-- In a real scenario, we'd clean them up first. 
-- For now, we assume data is clean or user handles errors.

ALTER TABLE public.operations_catalog
ADD CONSTRAINT operations_catalog_key_unique UNIQUE (operation_key);
