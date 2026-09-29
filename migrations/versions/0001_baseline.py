"""Baseline do schema anterior ao login federado."""

from alembic import op
import sqlalchemy as sa

revision = "0001_baseline"
down_revision = None
branch_labels = None
depends_on = None

TABLES = {"users", "lists", "movies", "comments", "draw_history", "user_lists_association"}


def upgrade() -> None:
    existing = set(sa.inspect(op.get_bind()).get_table_names())
    if TABLES & existing:
        if not TABLES.issubset(existing):
            missing = ", ".join(sorted(TABLES - existing))
            raise RuntimeError(f"Schema parcial detectado; tabelas ausentes: {missing}")
        return

    op.create_table("users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("password_hash", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"))
    op.create_index("ix_users_id", "users", ["id"])
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table("lists",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("code", sa.String(), nullable=True),
        sa.Column("owner_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"))
    op.create_index("ix_lists_id", "lists", ["id"])
    op.create_index("ix_lists_code", "lists", ["code"], unique=True)
    op.create_index("ix_lists_owner_id", "lists", ["owner_id"])

    op.create_table("user_lists_association",
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("list_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["list_id"], ["lists.id"]))
    op.create_index("ix_user_lists_association_user_id", "user_lists_association", ["user_id"])
    op.create_index("ix_user_lists_association_list_id", "user_lists_association", ["list_id"])

    op.create_table("movies",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("list_id", sa.Integer(), nullable=True),
        sa.Column("tmdbId", sa.Integer(), nullable=True),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("posterUrl", sa.String(), nullable=True),
        sa.Column("backdropUrl", sa.String(), nullable=True),
        sa.Column("synopsis", sa.String(), nullable=True),
        sa.Column("genres", sa.JSON(), nullable=True),
        sa.Column("releaseYear", sa.String(), nullable=True),
        sa.Column("runtime", sa.Integer(), nullable=True),
        sa.Column("tmdbRating", sa.Float(), nullable=True),
        sa.Column("watched", sa.Boolean(), nullable=True),
        sa.Column("watchProviders", sa.JSON(), nullable=True),
        sa.Column("trailerKey", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(["list_id"], ["lists.id"]),
        sa.PrimaryKeyConstraint("id"))
    for column in ("id", "list_id", "tmdbId"):
        op.create_index(f"ix_movies_{column}", "movies", [column])

    op.create_table("comments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("movie_id", sa.Integer(), nullable=True),
        sa.Column("user_id", sa.String(), nullable=True),
        sa.Column("user_name", sa.String(), nullable=True),
        sa.Column("text", sa.String(), nullable=True),
        sa.Column("rating", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(["movie_id"], ["movies.id"]),
        sa.PrimaryKeyConstraint("id"))
    op.create_index("ix_comments_id", "comments", ["id"])
    op.create_index("ix_comments_movie_id", "comments", ["movie_id"])

    op.create_table("draw_history",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("list_id", sa.Integer(), nullable=True),
        sa.Column("movie_id", sa.Integer(), nullable=True),
        sa.Column("movie_title", sa.String(), nullable=False),
        sa.Column("movie_poster", sa.String(), nullable=True),
        sa.Column("draw_type", sa.String(), nullable=True),
        sa.Column("drawn_by", sa.String(), nullable=True),
        sa.Column("drawn_at", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(["list_id"], ["lists.id"]),
        sa.ForeignKeyConstraint(["movie_id"], ["movies.id"]),
        sa.PrimaryKeyConstraint("id"))
    op.create_index("ix_draw_history_id", "draw_history", ["id"])
    op.create_index("ix_draw_history_list_id", "draw_history", ["list_id"])


def downgrade() -> None:
    for table in ("draw_history", "comments", "movies", "user_lists_association", "lists", "users"):
        op.drop_table(table)
