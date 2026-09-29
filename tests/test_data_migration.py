import pytest
import sqlalchemy as sa

from scripts.migrate_database import migrate_tables


def create_schema(engine, include_google_sub: bool) -> None:
    metadata = sa.MetaData()
    user_columns = [
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("email", sa.String, nullable=False),
        sa.Column("password_hash", sa.String, nullable=False),
    ]
    if include_google_sub:
        user_columns.append(sa.Column("google_sub", sa.String, nullable=True))
    sa.Table("users", metadata, *user_columns)
    sa.Table(
        "lists",
        metadata,
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String, nullable=False),
        sa.Column("code", sa.String),
        sa.Column("owner_id", sa.Integer, sa.ForeignKey("users.id")),
    )
    metadata.create_all(engine)


def test_migration_preserves_ids_and_accepts_new_nullable_columns(tmp_path):
    source = sa.create_engine(f"sqlite:///{tmp_path / 'source.db'}")
    destination = sa.create_engine(f"sqlite:///{tmp_path / 'destination.db'}")
    create_schema(source, include_google_sub=False)
    create_schema(destination, include_google_sub=True)

    with source.begin() as connection:
        connection.execute(
            sa.text("INSERT INTO users (id, email, password_hash) VALUES (7, 'owner@example.com', 'hash')")
        )
        connection.execute(
            sa.text("INSERT INTO lists (id, name, code, owner_id) VALUES (9, 'Filmes', 'ABC123', 7)")
        )

    result = migrate_tables(source, destination, ("users", "lists"))

    assert result == {"users": 1, "lists": 1}
    with destination.connect() as connection:
        user = connection.execute(sa.text("SELECT id, email, google_sub FROM users")).mappings().one()
        movie_list = connection.execute(sa.text("SELECT id, owner_id FROM lists")).mappings().one()
    assert dict(user) == {"id": 7, "email": "owner@example.com", "google_sub": None}
    assert dict(movie_list) == {"id": 9, "owner_id": 7}


def test_migration_refuses_to_overwrite_non_empty_destination(tmp_path):
    source = sa.create_engine(f"sqlite:///{tmp_path / 'source.db'}")
    destination = sa.create_engine(f"sqlite:///{tmp_path / 'destination.db'}")
    create_schema(source, include_google_sub=False)
    create_schema(destination, include_google_sub=True)
    with destination.begin() as connection:
        connection.execute(
            sa.text("INSERT INTO users (id, email, password_hash) VALUES (1, 'existing@example.com', 'hash')")
        )

    with pytest.raises(RuntimeError, match="destino não está vazio"):
        migrate_tables(source, destination, ("users", "lists"))
