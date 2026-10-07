-- ═══════════════════════════════════════════════════════════
-- Station One — Configurações do assistente e registro de uso
--
-- user_settings: a chave da API da Anthropic de cada pessoa, cifrada pelo
--   servidor (Fernet) — o banco nunca vê a chave em texto puro — e o modelo
--   que ela escolheu. Cada pessoa paga o próprio uso.
-- assistant_usage: tokens de cada chamada, para mostrar o gasto estimado.
-- ═══════════════════════════════════════════════════════════

create table if not exists user_settings (
  user_id                    uuid primary key references auth.users(id) on delete cascade,
  anthropic_key_ciphertext   text,
  anthropic_key_hint         text,           -- últimos 4 caracteres, para exibir
  assistant_model            text,           -- null = padrão do servidor
  updated_at                 timestamptz default now()
);

alter table user_settings enable row level security;
do $$ begin
  if not exists (select 1 from pg_policies where tablename = 'user_settings' and policyname = 'users_own_settings') then
    create policy "users_own_settings" on user_settings using (user_id = auth.uid());
  end if;
end $$;

create table if not exists assistant_usage (
  id             uuid primary key default gen_random_uuid(),
  user_id        uuid references auth.users(id) on delete cascade not null,
  created_at     timestamptz default now(),
  kind           text not null,              -- capture | chat | briefing | review
  model          text not null,
  input_tokens   integer not null default 0,
  output_tokens  integer not null default 0,
  cost_usd       numeric(10, 6) not null default 0
);

create index if not exists idx_assistant_usage_user_created on assistant_usage(user_id, created_at desc);
alter table assistant_usage enable row level security;
do $$ begin
  if not exists (select 1 from pg_policies where tablename = 'assistant_usage' and policyname = 'users_own_assistant_usage') then
    create policy "users_own_assistant_usage" on assistant_usage using (user_id = auth.uid());
  end if;
end $$;
