"""Aplica Alembic no Supabase usando o Session Pooler sem imprimir credenciais."""

import os

from alembic import command
from alembic.config import Config
from dotenv import dotenv_values

from scripts.inspect_databases import use_supabase_session_pooler


if __name__ == "__main__":
    config_values = dotenv_values(".env")
    database_url = config_values.get("DATABASE_URL")
    if not database_url:
        raise SystemExit("DATABASE_URL ausente")

    pooler_url = use_supabase_session_pooler(database_url)
    os.environ["DATABASE_URL"] = pooler_url.render_as_string(hide_password=False)
    command.upgrade(Config("alembic.ini"), "head")
    print("Supabase atualizado até o head do Alembic.")
