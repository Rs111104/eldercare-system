# Database

PostgreSQL/Supabase migrations for the ElderCare schema.

## Migrations
- `001_initial_schema.sql` — core tables, indexes, and constraints
- `002_seed_and_rls.sql` — seed rows and RLS policies
- `003_helper_functions.sql` — helper routines used by the app

## Apply migrations
```bash
supabase db push
```

If you prefer the Supabase SQL editor, apply the files in numeric order.

## Runtime notes
- Keep RLS enabled on sensitive tables.
- Use the service-role key only in trusted backend environments.
- Enable realtime only for tables that need live updates.

## Required env values
- `SUPABASE_URL`
- `SUPABASE_KEY`
- `SUPABASE_SERVICE_ROLE_KEY`
