-- Habilita Supabase Realtime (postgres_changes) para as tabelas que o
-- dashboard escuta em frontend/src/routes/+page.svelte.
-- Idempotente: só adiciona as tabelas que ainda não estão na publicação.
do $$
declare t text;
begin
  foreach t in array array['items','goals','milestones','wishlist','habits','habit_completions'] loop
    if not exists (
      select 1 from pg_publication_tables
      where pubname = 'supabase_realtime' and schemaname = 'public' and tablename = t
    ) then
      execute format('alter publication supabase_realtime add table public.%I', t);
    end if;
  end loop;
end $$;
