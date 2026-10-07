-- Prazo de tarefa é um dia do calendário, não um instante: como timestamptz,
-- "sexta 00:00 UTC" aparecia como quinta no Brasil. Converte para date
-- (no fuso de Brasília, caso exista algum valor). Idempotente.
do $$ begin
  if exists (
    select 1 from information_schema.columns
    where table_schema = 'public' and table_name = 'items'
      and column_name = 'due_date' and data_type <> 'date'
  ) then
    alter table items
      alter column due_date type date
      using (due_date at time zone 'America/Sao_Paulo')::date;
  end if;
end $$;

create index if not exists idx_items_user_due on items(user_id, due_date) where due_date is not null;
