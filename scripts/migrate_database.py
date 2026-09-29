"""Copia dados do PostgreSQL antigo para o Supabase em uma única transação."""

import hashlib
import json

import sqlalchemy as sa
from dotenv import dotenv_values

from scripts.inspect_databases import parse_database_url, use_supabase_session_pooler


TABLES = (
    "users",
    "lists",
    "user_lists_association",
    "movies",
    "comments",
    "draw_history",
)


def _digest(connection, table, columns) -> str:
    primary_key = list(table.primary_key.columns)
    order_columns = primary_key or columns
    statement = sa.select(*columns).order_by(*order_columns)
    digest = hashlib.sha256()
    for row in connection.execute(statement).mappings():
        payload = {column.name: row[column.name] for column in columns}
        digest.update(json.dumps(payload, default=str, sort_keys=True, ensure_ascii=False).encode("utf-8"))
        digest.update(b"\n")
    return digest.hexdigest()


def migrate_tables(source_engine, destination_engine, table_names=TABLES) -> dict[str, int]:
    source_metadata = sa.MetaData()
    destination_metadata = sa.MetaData()
    source_metadata.reflect(bind=source_engine, only=table_names)
    destination_metadata.reflect(bind=destination_engine, only=table_names)

    missing_source = set(table_names) - set(source_metadata.tables)
    missing_destination = set(table_names) - set(destination_metadata.tables)
    if missing_source or missing_destination:
        raise RuntimeError(
            f"schema incompleto; origem={sorted(missing_source)}, destino={sorted(missing_destination)}"
        )

    with source_engine.connect() as source, source.begin():
        with destination_engine.begin() as destination:
            non_empty = {
                name: destination.execute(sa.select(sa.func.count()).select_from(destination_metadata.tables[name])).scalar_one()
                for name in table_names
            }
            if any(non_empty.values()):
                raise RuntimeError(f"destino não está vazio: {non_empty}")

            counts = {}
            for name in table_names:
                source_table = source_metadata.tables[name]
                destination_table = destination_metadata.tables[name]
                columns = [
                    source_table.c[column.name]
                    for column in source_table.columns
                    if column.name in destination_table.c
                ]
                rows = [dict(row) for row in source.execute(sa.select(*columns)).mappings()]
                if rows:
                    destination.execute(destination_table.insert(), rows)
                counts[name] = len(rows)

                destination_columns = [destination_table.c[column.name] for column in columns]
                if _digest(source, source_table, columns) != _digest(destination, destination_table, destination_columns):
                    raise RuntimeError(f"validação de conteúdo falhou para {name}")

                if destination_engine.dialect.name == "postgresql" and "id" in destination_table.c:
                    sequence = destination.execute(
                        sa.text("SELECT pg_get_serial_sequence(:table_name, 'id')"),
                        {"table_name": name},
                    ).scalar_one_or_none()
                    if sequence:
                        destination.execute(
                            sa.text(
                                f'SELECT setval(CAST(:sequence AS regclass), '
                                f'COALESCE(MAX(id), 1), COUNT(*) > 0) FROM "{name}"'
                            ),
                            {"sequence": sequence},
                        )

            return counts


if __name__ == "__main__":
    config = dotenv_values(".env")
    source_url = config.get("OLD_DATABASE_URL")
    destination_url = config.get("DATABASE_URL")
    if not source_url or not destination_url:
        raise SystemExit("OLD_DATABASE_URL e DATABASE_URL são obrigatórias")

    source_engine = sa.create_engine(
        parse_database_url(source_url),
        pool_pre_ping=True,
        isolation_level="REPEATABLE READ",
        connect_args={"connect_timeout": 8},
    )
    destination_engine = sa.create_engine(
        use_supabase_session_pooler(destination_url),
        pool_pre_ping=True,
        connect_args={"connect_timeout": 8},
    )
    try:
        migrated = migrate_tables(source_engine, destination_engine)
        print(f"Migração concluída e validada: {migrated}")
    finally:
        source_engine.dispose()
        destination_engine.dispose()
