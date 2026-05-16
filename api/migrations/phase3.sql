-- ═══════════════════════════════════════════════════════════
-- Station One — Phase 3 Migration
-- Rodar no SQL Editor do Supabase APÓS o init.sql
-- ═══════════════════════════════════════════════════════════

-- ── 3.2 Log da Estação ──────────────────────────────────────

CREATE TABLE IF NOT EXISTS daily_logs (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id     UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
  date        DATE NOT NULL DEFAULT CURRENT_DATE,
  content     TEXT NOT NULL DEFAULT '',
  created_at  TIMESTAMPTZ DEFAULT now(),
  updated_at  TIMESTAMPTZ DEFAULT now(),
  UNIQUE(user_id, date)
);

CREATE INDEX IF NOT EXISTS idx_daily_logs_user_date ON daily_logs(user_id, date DESC);
ALTER TABLE daily_logs ENABLE ROW LEVEL SECURITY;
CREATE POLICY "users_own_daily_logs" ON daily_logs USING (user_id = auth.uid());

-- ── 3.1 Protocolos (Hábitos) ────────────────────────────────

CREATE TABLE IF NOT EXISTS habits (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id     UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
  name        TEXT NOT NULL,
  emoji       TEXT DEFAULT '⚡',
  created_at  TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS habit_completions (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id     UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
  habit_id    UUID REFERENCES habits(id) ON DELETE CASCADE NOT NULL,
  date        DATE NOT NULL DEFAULT CURRENT_DATE,
  created_at  TIMESTAMPTZ DEFAULT now(),
  UNIQUE(user_id, habit_id, date)
);

CREATE INDEX IF NOT EXISTS idx_habits_user ON habits(user_id);
CREATE INDEX IF NOT EXISTS idx_habit_completions_habit_date ON habit_completions(habit_id, date DESC);

ALTER TABLE habits ENABLE ROW LEVEL SECURITY;
ALTER TABLE habit_completions ENABLE ROW LEVEL SECURITY;
CREATE POLICY "users_own_habits" ON habits USING (user_id = auth.uid());
CREATE POLICY "users_own_habit_completions" ON habit_completions USING (user_id = auth.uid());
