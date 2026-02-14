-- =========================================================
-- 🧹 Clean Up Duplicates in operations_catalog
-- =========================================================
-- This script keeps the MOST RECENT entry for each operation_key
-- and deletes older duplicates.
-- It resolves ERROR: 23505 (duplicate key value violates unique constraint)

DELETE FROM public.operations_catalog
WHERE id IN (
    SELECT id
    FROM (
        SELECT id,
               ROW_NUMBER() OVER (
                   PARTITION BY operation_key
                   ORDER BY updated_at DESC, created_at DESC, id DESC
               ) as row_num
        FROM public.operations_catalog
        WHERE operation_key IS NOT NULL
    ) t
    WHERE t.row_num > 1
);

-- After running this, re-run migration_add_unique_key.sql
