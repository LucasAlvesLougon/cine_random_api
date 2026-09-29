"""Inspeciona origem e destino sem imprimir URLs ou credenciais."""

from dotenv import dotenv_values
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import URL, make_url
from urllib.parse import parse_qsl, urlsplit

from database.connection import normalize_database_url


TABLES = (
    "users",
    "lists",
    "user_lists_association",
    "movies",
    "comments",
    "draw_history",
)


def parse_database_url(database_url: str) -> URL:
    """Aceita senhas com caracteres reservados mesmo quando não foram percent-encoded."""
    normalized = normalize_database_url(database_url)
    parsed = make_url(normalized)
    if parsed.host and "@" not in parsed.host:
        return parsed

    credentials, address = normalized.rsplit("@", 1)
    driver, user_password = credentials.split("://", 1)
    username, password = user_password.split(":", 1)
    address_parts = urlsplit(f"postgresql://{address}")
    return URL.create(
        drivername=driver,
        username=username,
        password=password,
        host=address_parts.hostname,
        port=address_parts.port,
        database=address_parts.path.lstrip("/"),
        query=dict(parse_qsl(address_parts.query)),
    )


def use_supabase_session_pooler(database_url: str) -> URL:
    """Converte a URL direta IPv6 deste projeto para o Session Pooler IPv4."""
    url = parse_database_url(database_url)
    project_ref = "pofbjclkawmddmyaxisu"
    if url.host == f"db.{project_ref}.supabase.co":
        return url.set(
            host="aws-0-us-east-1.pooler.supabase.com",
            port=5432,
            username=f"postgres.{project_ref}",
        )
    return url


def inspect_database(label: str, database_url: str | URL | None) -> None:
    if not database_url:
        print(f"{label}: URL ausente")
        return

    engine = None
    try:
        engine = create_engine(
            parse_database_url(database_url) if isinstance(database_url, str) else database_url,
            pool_pre_ping=True,
            connect_args={"connect_timeout": 8},
        )
        with engine.connect() as connection:
            existing = set(inspect(connection).get_table_names(schema="public"))
            counts = {
                table: connection.execute(text(f'SELECT COUNT(*) FROM "{table}"')).scalar_one()
                for table in TABLES
                if table in existing
            }
            print(f"{label}: conexão OK; tabelas={sorted(existing)}; contagens={counts}")
            if connection.dialect.name == "postgresql" and TABLES[0] in existing:
                rls = dict(
                    connection.execute(
                        text(
                            "SELECT relname, relrowsecurity FROM pg_class "
                            "WHERE relnamespace = 'public'::regnamespace AND relname = ANY(:tables)"
                        ),
                        {"tables": list(TABLES)},
                    ).all()
                )
                version = (
                    connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one_or_none()
                    if "alembic_version" in existing
                    else "não versionado"
                )
                movie_fk_index = any(
                    index["name"] == "ix_draw_history_movie_id"
                    for index in inspect(connection).get_indexes("draw_history")
                )
                print(f"{label}: alembic={version}; rls={rls}; draw_history.movie_id_index={movie_fk_index}")
    except Exception as exc:
        detail = str(getattr(exc, "orig", exc)).lower()
        if "password authentication failed" in detail:
            category = "autenticação recusada"
        elif "network is unreachable" in detail or "no route to host" in detail:
            category = "host direto sem rota IPv4; use o pooler do Supabase"
        elif "could not translate host" in detail or "name or service not known" in detail:
            category = "DNS/host inválido"
        elif "timeout" in detail:
            category = "timeout de conexão"
        else:
            try:
                secret = parse_database_url(database_url).password if isinstance(database_url, str) else database_url.password
            except Exception:
                secret = None
            sanitized = str(getattr(exc, "orig", exc))
            if secret:
                sanitized = sanitized.replace(secret, "***")
            category = sanitized.replace("\n", " ")[:300]
        print(f"{label}: falha ({category})")
    finally:
        if engine is not None:
            engine.dispose()


if __name__ == "__main__":
    config = dotenv_values(".env")
    inspect_database("origem", config.get("OLD_DATABASE_URL"))
    destination_url = config.get("DATABASE_URL")
    inspect_database("destino", use_supabase_session_pooler(destination_url) if destination_url else None)
