"""Permite arquivar histórico sem apagar os registros."""

from alembic import op
import sqlalchemy as sa

revision = "0006_archive_draw_history"
down_revision = "0005_password_reset_tokens"
branch_labels = None
depends_on = None


def upgrade() -> None:
    columns = {column["name"] for column in sa.inspect(op.get_bind()).get_columns("draw_history")}
    if "archived_at" not in columns:
        op.add_column("draw_history", sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    columns = {column["name"] for column in sa.inspect(op.get_bind()).get_columns("draw_history")}
    if "archived_at" in columns:
        op.drop_column("draw_history", "archived_at")
