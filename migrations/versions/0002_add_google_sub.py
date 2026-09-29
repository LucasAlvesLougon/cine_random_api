"""Adiciona o identificador federado imutável do Google."""

from alembic import op
import sqlalchemy as sa

revision = "0002_add_google_sub"
down_revision = "0001_baseline"
branch_labels = None
depends_on = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    columns = {column["name"] for column in inspector.get_columns("users")}
    if "google_sub" not in columns:
        op.add_column("users", sa.Column("google_sub", sa.String(), nullable=True))
    indexes = {index["name"] for index in sa.inspect(op.get_bind()).get_indexes("users")}
    if "ix_users_google_sub" not in indexes:
        op.create_index("ix_users_google_sub", "users", ["google_sub"], unique=True)


def downgrade() -> None:
    indexes = {index["name"] for index in sa.inspect(op.get_bind()).get_indexes("users")}
    if "ix_users_google_sub" in indexes:
        op.drop_index("ix_users_google_sub", table_name="users")
    columns = {column["name"] for column in sa.inspect(op.get_bind()).get_columns("users")}
    if "google_sub" in columns:
        op.drop_column("users", "google_sub")
