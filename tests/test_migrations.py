from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect


def test_migrations_create_and_rollback_google_identity(tmp_path, monkeypatch):
    database_path = tmp_path / "migration.db"
    database_url = f"sqlite:///{database_path.as_posix()}"
    monkeypatch.setenv("DATABASE_URL", database_url)
    config = Config("alembic.ini")

    command.upgrade(config, "head")
    inspector = inspect(create_engine(database_url))
    assert "google_sub" in {column["name"] for column in inspector.get_columns("users")}
    google_index = next(index for index in inspector.get_indexes("users") if index["name"] == "ix_users_google_sub")
    assert google_index["unique"] == 1

    command.downgrade(config, "0001_baseline")
    inspector = inspect(create_engine(database_url))
    assert "google_sub" not in {column["name"] for column in inspector.get_columns("users")}

    command.upgrade(config, "head")
    inspector = inspect(create_engine(database_url))
    assert "google_sub" in {column["name"] for column in inspector.get_columns("users")}


def test_migrations_adopt_existing_unversioned_database(tmp_path, monkeypatch):
    database_path = tmp_path / "existing.db"
    database_url = f"sqlite:///{database_path.as_posix()}"
    monkeypatch.setenv("DATABASE_URL", database_url)
    config = Config("alembic.ini")
    command.upgrade(config, "0001_baseline")

    engine = create_engine(database_url)
    with engine.begin() as connection:
        connection.exec_driver_sql(
            "INSERT INTO users (email, password_hash) VALUES ('preserved@example.com', 'hash')"
        )
        connection.exec_driver_sql("DROP TABLE alembic_version")

    command.upgrade(config, "head")

    with engine.connect() as connection:
        preserved = connection.exec_driver_sql(
            "SELECT email FROM users WHERE email = 'preserved@example.com'"
        ).scalar_one()
    assert preserved == "preserved@example.com"
    assert "google_sub" in {column["name"] for column in inspect(engine).get_columns("users")}
