"""Adiciona constraints contra membros e filmes duplicados."""

from alembic import op
import sqlalchemy as sa

revision = "0004_integrity_constraints"
down_revision = "0003_harden_public_schema"
branch_labels = None
depends_on = None


def _assert_no_duplicates(bind) -> None:
    duplicate_members = bind.execute(sa.text(
        """
        SELECT user_id, list_id, COUNT(*) AS total
        FROM user_lists_association
        GROUP BY user_id, list_id
        HAVING COUNT(*) > 1
        """
    )).fetchall()
    duplicate_movies = bind.execute(sa.text(
        """
        SELECT list_id, "tmdbId", COUNT(*) AS total
        FROM movies
        GROUP BY list_id, "tmdbId"
        HAVING COUNT(*) > 1
        """
    )).fetchall()
    if duplicate_members or duplicate_movies:
        raise RuntimeError(
            "Não foi possível aplicar as constraints: existem membros ou filmes duplicados. "
            "Resolva os duplicados e execute a migration novamente."
        )


def upgrade() -> None:
    bind = op.get_bind()
    _assert_no_duplicates(bind)
    existing_association_indexes = {
        index["name"] for index in sa.inspect(bind).get_indexes("user_lists_association")
    }
    if "uq_user_lists_user_list" not in existing_association_indexes:
        op.create_index(
            "uq_user_lists_user_list",
            "user_lists_association",
            ["user_id", "list_id"],
            unique=True,
        )

    existing_movie_indexes = {
        index["name"] for index in sa.inspect(bind).get_indexes("movies")
    }
    if "uq_movies_list_tmdb" not in existing_movie_indexes:
        op.create_index(
            "uq_movies_list_tmdb",
            "movies",
            ["list_id", "tmdbId"],
            unique=True,
        )


def downgrade() -> None:
    bind = op.get_bind()
    for table, index_name in (
        ("movies", "uq_movies_list_tmdb"),
        ("user_lists_association", "uq_user_lists_user_list"),
    ):
        if index_name in {index["name"] for index in sa.inspect(bind).get_indexes(table)}:
            op.drop_index(index_name, table_name=table)
