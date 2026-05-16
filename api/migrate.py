#!/usr/bin/env python3
"""
migrate.py — Station One Migration Runner
==========================================
Aplica todos os arquivos .sql de migrations/ que ainda não foram executados.
Usa a mesma DATABASE_URL do .env e mantém um registro na tabela schema_migrations.

Uso:
    python migrate.py                    # aplica migrações pendentes
    python migrate.py --status           # lista o estado de cada migration
    python migrate.py --mark <arquivo>   # marca uma migration como aplicada SEM rodá-la
                                         # (útil para migrations já executadas manualmente)
"""

import asyncio
import hashlib
import os
import sys
from pathlib import Path

import asyncpg

# ─── Carrega .env sem precisar de python-dotenv ───────────────────────────────
_env_file = Path(__file__).parent / ".env"
if _env_file.exists():
    for _line in _env_file.read_text().splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _key, _, _val = _line.partition("=")
            os.environ.setdefault(_key.strip(), _val.strip().strip('"').strip("'"))

MIGRATIONS_DIR = Path(__file__).parent / "migrations"


def _pg_url(url: str) -> str:
    """asyncpg usa postgresql://, não postgresql+asyncpg://"""
    return url.replace("postgresql+asyncpg://", "postgresql://")


async def ensure_migrations_table(conn: asyncpg.Connection):
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS schema_migrations (
            filename   TEXT PRIMARY KEY,
            checksum   TEXT NOT NULL,
            applied_at TIMESTAMPTZ DEFAULT now()
        )
    """)


async def get_applied(conn: asyncpg.Connection) -> set[str]:
    rows = await conn.fetch("SELECT filename FROM schema_migrations")
    return {r["filename"] for r in rows}


async def connect() -> asyncpg.Connection:
    url = _pg_url(os.environ["DATABASE_URL"])
    return await asyncpg.connect(url, ssl="require", statement_cache_size=0)


# ─── Comandos ─────────────────────────────────────────────────────────────────

async def cmd_status():
    conn = await connect()
    try:
        await ensure_migrations_table(conn)
        applied = await get_applied(conn)
        sql_files = sorted(MIGRATIONS_DIR.glob("*.sql"))
        print(f"\n{'STATUS':<14} {'ARQUIVO'}")
        print("-" * 55)
        for f in sql_files:
            tag = "✅ aplicado" if f.name in applied else "⏳ pendente"
            print(f"{tag:<18} {f.name}")
        print()
    finally:
        await conn.close()


async def cmd_mark(filename: str):
    """Marca uma migration como aplicada sem executá-la (para migrations já rodadas manualmente)."""
    target = MIGRATIONS_DIR / filename
    if not target.exists():
        print(f"❌ Arquivo não encontrado: migrations/{filename}")
        sys.exit(1)

    sql = target.read_text(encoding="utf-8")
    checksum = hashlib.sha256(sql.encode()).hexdigest()[:16]

    conn = await connect()
    try:
        await ensure_migrations_table(conn)
        applied = await get_applied(conn)
        if filename in applied:
            print(f"ℹ️  {filename} já estava marcada como aplicada.")
            return
        await conn.execute(
            "INSERT INTO schema_migrations (filename, checksum) VALUES ($1, $2)",
            filename, checksum
        )
        print(f"✅ {filename} marcada como aplicada.")
    finally:
        await conn.close()


async def cmd_run():
    conn = await connect()
    try:
        await ensure_migrations_table(conn)
        applied = await get_applied(conn)
        sql_files = sorted(MIGRATIONS_DIR.glob("*.sql"))

        if not sql_files:
            print("⚠️  Nenhum arquivo .sql encontrado em migrations/")
            return

        pending = [f for f in sql_files if f.name not in applied]

        if not pending:
            print("✅ Todas as migrations já foram aplicadas.")
            return

        print(f"\n🚀 Aplicando {len(pending)} migration(s)...\n")

        for filepath in pending:
            sql = filepath.read_text(encoding="utf-8")
            checksum = hashlib.sha256(sql.encode()).hexdigest()[:16]
            print(f"  ▶ {filepath.name} ... ", end="", flush=True)
            try:
                async with conn.transaction():
                    await conn.execute(sql)
                    await conn.execute(
                        "INSERT INTO schema_migrations (filename, checksum) VALUES ($1, $2)",
                        filepath.name, checksum,
                    )
                print("✅")
            except Exception as e:
                print(f"❌\n\nErro em {filepath.name}:\n{e}")
                sys.exit(1)

        print(f"\n✅ {len(pending)} migration(s) aplicada(s) com sucesso!\n")

    finally:
        await conn.close()


# ─── Entry point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    args = sys.argv[1:]

    if "--status" in args:
        asyncio.run(cmd_status())
    elif "--mark" in args:
        idx = args.index("--mark")
        if idx + 1 >= len(args):
            print("Uso: python migrate.py --mark <nome_do_arquivo.sql>")
            sys.exit(1)
        asyncio.run(cmd_mark(args[idx + 1]))
    else:
        asyncio.run(cmd_run())
