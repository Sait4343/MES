-- ==========================================
-- 👮 Grant Admin Role Script
-- ==========================================

-- 1. Replace 'your_email@example.com' with the email you used to sign up/login.
-- 2. Run this script in Supabase SQL Editor.

UPDATE public.profiles
SET role = 'admin'
WHERE email = 'your_email@example.com';

-- Verify the change
SELECT * FROM public.profiles WHERE role = 'admin';
