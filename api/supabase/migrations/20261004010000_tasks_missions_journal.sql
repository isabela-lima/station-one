-- ═══════════════════════════════════════════════════════════
-- Station One — Tarefas por missão + Diário de bordo
--
-- Aditiva: não apaga nada. Copia marcos → tarefas e notas/links → entradas
-- do diário reaproveitando os mesmos IDs, então rodar de novo é seguro.
-- As tabelas/linhas antigas (milestones, items do tipo note/link) ficam
-- intactas até uma limpeza posterior.
-- ═══════════════════════════════════════════════════════════

-- ── Tarefas podem pertencer a uma missão ────────────────────
alter table items add column if not exists goal_id uuid references goals(id) on delete set null;
alter table items add column if not exists completed_at timestamptz;

create index if not exists idx_items_user_goal on items(user_id, goal_id);
create index if not exists idx_items_user_completed_at on items(user_id, completed_at);

-- Tarefas já concluídas: sem data real, usamos a de criação
update items set completed_at = created_at where completed and completed_at is null;

-- Marcos viram tarefas da missão (mesmo id)
insert into items (id, user_id, type, content, completed, priority, goal_id, completed_at, created_at)
select m.id, m.user_id, 'task', m.title, coalesce(m.completed, false), false, m.goal_id,
       case when m.completed then m.created_at end, m.created_at
from milestones m
where not exists (select 1 from items i where i.id = m.id);

-- ── Diário de bordo: entradas com hora ──────────────────────
create table if not exists log_entries (
  id          uuid primary key default gen_random_uuid(),
  user_id     uuid references auth.users(id) on delete cascade not null,
  date        date not null,
  content     text not null,
  url         text,
  created_at  timestamptz default now()
);

create index if not exists idx_log_entries_user_date on log_entries(user_id, date desc, created_at desc);
alter table log_entries enable row level security;
do $$ begin
  if not exists (select 1 from pg_policies where tablename = 'log_entries' and policyname = 'users_own_log_entries') then
    create policy "users_own_log_entries" on log_entries using (user_id = auth.uid());
  end if;
end $$;

-- Notas e links de Operações viram entradas do diário (mesmo id).
-- O dia é calculado no fuso de Brasília.
insert into log_entries (id, user_id, date, content, url, created_at)
select i.id, i.user_id,
       (i.created_at at time zone 'America/Sao_Paulo')::date,
       case when i.type = 'link' then coalesce(nullif(trim(i.title), ''), i.content) else i.content end,
       case when i.type = 'link' then i.content end,
       i.created_at
from items i
where i.type in ('note', 'link')
  and not exists (select 1 from log_entries e where e.id = i.id);

-- ── Check-in diário: humor e energia (1–5) ──────────────────
alter table daily_logs add column if not exists mood smallint check (mood between 1 and 5);
alter table daily_logs add column if not exists energy smallint check (energy between 1 and 5);

-- ── Realtime para o diário ──────────────────────────────────
do $$ begin
  if not exists (
    select 1 from pg_publication_tables
    where pubname = 'supabase_realtime' and schemaname = 'public' and tablename = 'log_entries'
  ) then
    alter publication supabase_realtime add table public.log_entries;
  end if;
end $$;
