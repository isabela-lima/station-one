from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    supabase_url: str
    supabase_secret_key: str          # Supabase publishable or secret key
    supabase_jwt_secret: str = ""     # Legacy HS256 secret — empty for RS256/JWKS projects
    database_url: str
    environment: str = "development"
    # Imprime cada SQL com os valores (diário, gastos…). Só para depurar: liga com SQL_ECHO=true
    sql_echo: bool = False
    cors_origins: str = "http://localhost:5173"
    # Chave Fernet que cifra as chaves da Anthropic dos usuários. Opcional: sem ela,
    # o servidor gera e guarda uma em api/.app_key (ver secrets_box.py).
    app_encryption_key: str = ""
    # Modelo do assistente quando o usuário não escolheu outro
    assistant_default_model: str = "claude-haiku-4-5"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",")]


settings = Settings()
