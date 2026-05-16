-- ═══════════════════════════════════════════════════════════
-- Station One — Schema Completo
-- Rodar no SQL Editor do Supabase (supabase.com → SQL Editor)
-- ═══════════════════════════════════════════════════════════

-- ── DADOS EXISTENTES (migração do PocketBase) ───────────────

CREATE TABLE IF NOT EXISTS items (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id     UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
  type        TEXT NOT NULL CHECK (type IN ('note', 'task', 'link')),
  content     TEXT NOT NULL,
  title       TEXT,
  completed   BOOLEAN DEFAULT FALSE,
  priority    BOOLEAN DEFAULT FALSE,
  due_date    TIMESTAMPTZ,
  created_at  TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS goals (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id     UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
  title       TEXT NOT NULL,
  created_at  TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS milestones (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id     UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
  goal_id     UUID REFERENCES goals(id) ON DELETE CASCADE NOT NULL,
  title       TEXT NOT NULL,
  completed   BOOLEAN DEFAULT FALSE,
  created_at  TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS wishlist (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id       UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
  title         TEXT NOT NULL,
  url           TEXT NOT NULL,
  image_url     TEXT,
  description   TEXT,
  current_price DECIMAL(12,2) DEFAULT 0,
  target_price  DECIMAL(12,2) DEFAULT 0,
  currency      CHAR(3) DEFAULT 'BRL',
  created_at    TIMESTAMPTZ DEFAULT now()
);

-- ── FINANCIAL CORE (novo) ───────────────────────────────────

CREATE TABLE IF NOT EXISTS wallets (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id     UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
  name        TEXT NOT NULL,
  type        TEXT NOT NULL CHECK (type IN ('cash', 'vr', 'inflow')),
  emoji       TEXT DEFAULT '💵',
  currency    CHAR(3) DEFAULT 'BRL',
  created_at  TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS transactions (
  id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id            UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
  wallet_id          UUID REFERENCES wallets(id),
  amount             DECIMAL(12,2) NOT NULL,
  currency           CHAR(3) DEFAULT 'BRL',
  category           TEXT NOT NULL,
  description        TEXT,
  suggested_wallet_id UUID REFERENCES wallets(id),
  date               DATE NOT NULL DEFAULT CURRENT_DATE,
  is_recurring       BOOLEAN DEFAULT FALSE,
  parent_id          UUID REFERENCES transactions(id),
  installment_num    INT,
  total_installments INT,
  created_at         TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS budgets (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id      UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
  wallet_id    UUID REFERENCES wallets(id),
  category     TEXT NOT NULL,
  limit_amount DECIMAL(12,2) NOT NULL,
  currency     CHAR(3) DEFAULT 'BRL',
  period       TEXT DEFAULT 'monthly'
);

CREATE TABLE IF NOT EXISTS debts (
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id          UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
  name             TEXT NOT NULL,
  original_amount  DECIMAL(12,2) NOT NULL,
  current_amount   DECIMAL(12,2) NOT NULL,
  monthly_payment  DECIMAL(12,2) NOT NULL,
  currency         CHAR(3) DEFAULT 'BRL',
  start_date       DATE NOT NULL,
  created_at       TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS health_logs (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id       UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
  date          DATE NOT NULL DEFAULT CURRENT_DATE,
  trained       BOOLEAN DEFAULT FALSE,
  hrv_score     INT,
  energy_level  INT CHECK (energy_level BETWEEN 1 AND 5),
  notes         TEXT,
  created_at    TIMESTAMPTZ DEFAULT now(),
  UNIQUE(user_id, date)
);

-- ── ÍNDICES para performance ───────────────────────────────

CREATE INDEX IF NOT EXISTS idx_items_user ON items(user_id);
CREATE INDEX IF NOT EXISTS idx_items_type ON items(user_id, type);
CREATE INDEX IF NOT EXISTS idx_goals_user ON goals(user_id);
CREATE INDEX IF NOT EXISTS idx_milestones_goal ON milestones(goal_id);
CREATE INDEX IF NOT EXISTS idx_wishlist_user ON wishlist(user_id);
CREATE INDEX IF NOT EXISTS idx_wallets_user ON wallets(user_id);
CREATE INDEX IF NOT EXISTS idx_transactions_user ON transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(user_id, date DESC);
CREATE INDEX IF NOT EXISTS idx_debts_user ON debts(user_id);
CREATE INDEX IF NOT EXISTS idx_health_logs_user_date ON health_logs(user_id, date DESC);

-- ── ROW LEVEL SECURITY ─────────────────────────────────────
-- Garante que cada usuário só acessa os próprios dados

ALTER TABLE items ENABLE ROW LEVEL SECURITY;
ALTER TABLE goals ENABLE ROW LEVEL SECURITY;
ALTER TABLE milestones ENABLE ROW LEVEL SECURITY;
ALTER TABLE wishlist ENABLE ROW LEVEL SECURITY;
ALTER TABLE wallets ENABLE ROW LEVEL SECURITY;
ALTER TABLE transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE budgets ENABLE ROW LEVEL SECURITY;
ALTER TABLE debts ENABLE ROW LEVEL SECURITY;
ALTER TABLE health_logs ENABLE ROW LEVEL SECURITY;

-- Policies (allow all for authenticated owner)

CREATE POLICY "users_own_items" ON items USING (user_id = auth.uid());
CREATE POLICY "users_own_goals" ON goals USING (user_id = auth.uid());
CREATE POLICY "users_own_milestones" ON milestones USING (user_id = auth.uid());
CREATE POLICY "users_own_wishlist" ON wishlist USING (user_id = auth.uid());
CREATE POLICY "users_own_wallets" ON wallets USING (user_id = auth.uid());
CREATE POLICY "users_own_transactions" ON transactions USING (user_id = auth.uid());
CREATE POLICY "users_own_budgets" ON budgets USING (user_id = auth.uid());
CREATE POLICY "users_own_debts" ON debts USING (user_id = auth.uid());
CREATE POLICY "users_own_health_logs" ON health_logs USING (user_id = auth.uid());
