---
name: supabase-expert
description: Best practices for Supabase, RLS policies, Next.js integration, and database schema design.
---

# Supabase Development Standards

When writing code for Supabase, especially within Next.js applications, follow these guidelines:

### 1. Row Level Security (RLS) is Mandatory
- **Never** leave a table without RLS enabled.
- **Policies**: Always define separate policies for SELECT, INSERT, UPDATE, DELETE.
- **Auth**: Use `auth.uid()` for user-scoped data.
- **Service Role**: Do NOT use the `service_role` key in client-side code.

### 2. Next.js Integration (App Router)
- Use `@supabase/ssr` (or latest auth helpers) for creating clients in Server Components vs Client Components.
- **Server Components**: Fetch data directly without `useEffect`. Use `cookies()` to initialize the client.
- **Client Components**: Use singleton pattern for the Supabase client to avoid recreating it on every render.

### 3. Database Schema & Types
- **Snake_case** for table and column names in Postgres.
- **CamelCase** for JavaScript/TypeScript variables.
- Always generate TypeScript definitions using `supabase gen types` and use `Database` interface in your code.
- **Foreign Keys**: Always define foreign keys with `ON DELETE CASCADE` or `SET NULL` where appropriate to maintain referential integrity.

### 4. Performance
- **Select specific columns**: Avoid `select('*')` in production; list explicitly needed columns.
- **Indexes**: Suggest creating indexes for columns frequently used in `WHERE` and `JOIN` clauses.
