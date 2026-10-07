-- ═══════════════════════════════════════════════════════════
-- Station One — Limpeza dos dados legados
--
-- Remove o que a migração 20261004010000_tasks_missions_journal copiou
-- para os novos modelos e que nada mais usa:
--   • tabela milestones          → virou items (type='task', goal_id)
--   • items do tipo note/link    → viraram log_entries
--   • daily_logs.content         → substituído por log_entries
--
-- Seguro por construção: aborta sem apagar nada se encontrar qualquer
-- linha antiga sem a cópia correspondente (mesmo id) ou texto livre no log.
-- ═══════════════════════════════════════════════════════════

do $$
declare
  missing_milestones int := 0;
  missing_notes int;
  nonempty_logs int := 0;
begin
  if to_regclass('public.milestones') is not null then
    select count(*) into missing_milestones
    from milestones m
    where not exists (select 1 from items i where i.id = m.id and i.type = 'task');
  end if;

  select count(*) into missing_notes
  from items i
  where i.type in ('note', 'link')
    and not exists (select 1 from log_entries e where e.id = i.id);

  if exists (select 1 from information_schema.columns
             where table_schema = 'public' and table_name = 'daily_logs' and column_name = 'content') then
    execute 'select count(*) from daily_logs where length(trim(content)) > 0' into nonempty_logs;
  end if;

  if missing_milestones > 0 or missing_notes > 0 or nonempty_logs > 0 then
    raise exception 'Limpeza abortada: % marco(s) e % nota(s)/link(s) sem cópia, % log(s) com texto livre',
      missing_milestones, missing_notes, nonempty_logs;
  end if;
end $$;

-- Remove a tabela (as políticas e a entrada na publicação de Realtime vão junto)
drop table if exists milestones;

delete from items where type in ('note', 'link');

alter table daily_logs drop column if exists content;
