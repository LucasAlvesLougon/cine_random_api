"""Protege o schema público e completa índices de chaves estrangeiras."""

from alembic import op
import sqlalchemy as sa

revision = "0003_harden_public_schema"
down_revision = "0002_add_google_sub"
branch_labels = None
depends_on = None

TABLES = (
    "users",
    "lists",
    "user_lists_association",
    "movies",
    "comments",
    "draw_history",
)


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return

    indexes = {index["name"] for index in sa.inspect(bind).get_indexes("draw_history")}
    if "ix_draw_history_movie_id" not in indexes:
        op.create_index("ix_draw_history_movie_id", "draw_history", ["movie_id"])

    for table in TABLES:
        op.execute(sa.text(f'ALTER TABLE "{table}" ENABLE ROW LEVEL SECURITY'))

    op.execute(
        sa.text(
            """
            DO $$
            BEGIN
                IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'anon') THEN
                    REVOKE ALL ON ALL TABLES IN SCHEMA public FROM anon;
                    REVOKE ALL ON ALL SEQUENCES IN SCHEMA public FROM anon;
                END IF;
                IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'authenticated') THEN
                    REVOKE ALL ON ALL TABLES IN SCHEMA public FROM authenticated;
                    REVOKE ALL ON ALL SEQUENCES IN SCHEMA public FROM authenticated;
                END IF;
            END
            $$;
            """
        )
    )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return

    for table in TABLES:
        op.execute(sa.text(f'ALTER TABLE "{table}" DISABLE ROW LEVEL SECURITY'))

    indexes = {index["name"] for index in sa.inspect(bind).get_indexes("draw_history")}
    if "ix_draw_history_movie_id" in indexes:
        op.drop_index("ix_draw_history_movie_id", table_name="draw_history")
