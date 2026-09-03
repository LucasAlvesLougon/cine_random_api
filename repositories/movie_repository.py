from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta
from models.models import Movie, MovieList, User, Comment, DrawHistory

class MovieRepository:
    def __init__(self, db: Session):
        self.db = db

    # --- Listas ---
    def get_lists_for_user(self, user: User) -> List[MovieList]:
        """Retorna todas as listas que o usuário é dono ou membro de forma eficiente."""
        return (
            self.db.query(MovieList)
            .filter(
                (MovieList.owner_id == user.id) | 
                (MovieList.members.any(User.id == user.id))
            )
            .distinct()
            .all()
        )

    def get_list_by_code(self, code: str) -> Optional[MovieList]:
        """Busca uma lista pelo código único."""
        return self.db.query(MovieList).filter(MovieList.code == code).first()

    def create_list(self, name: str, code: str, owner: User) -> MovieList:
        """Cria e persiste uma nova lista de filmes."""
        new_list = MovieList(name=name, code=code, owner_id=owner.id)
        new_list.members.append(owner)
        self.db.add(new_list)
        self.db.commit()
        self.db.refresh(new_list)
        return new_list

    def update_list_name(self, movie_list: MovieList, new_name: str) -> MovieList:
        """Atualiza o nome da lista."""
        movie_list.name = new_name
        self.db.commit()
        self.db.refresh(movie_list)
        return movie_list

    def delete_list(self, movie_list: MovieList) -> None:
        """Exclui com segurança a lista e todos os filmes, comentários, histórico e associações via cascade."""
        # 1. Limpa associação de membros da lista
        movie_list.members.clear()

        # 2. Remove a lista (o cascade 'all, delete-orphan' remove filmes, comentários e draw_history em ordem)
        self.db.delete(movie_list)
        self.db.commit()

    def add_member_to_list(self, movie_list: MovieList, user: User) -> MovieList:
        """Adiciona um usuário como membro de uma lista."""
        movie_list.members.append(user)
        self.db.commit()
        self.db.refresh(movie_list)
        return movie_list

    def get_members_of_list(self, movie_list: MovieList) -> List[dict]:
        """Retorna todos os membros da lista identificando o dono."""
        members = []
        for user in movie_list.members:
            members.append({
                "id": user.id,
                "email": user.email,
                "is_owner": user.id == movie_list.owner_id
            })
        if movie_list.owner and not any(m["id"] == movie_list.owner.id for m in members):
            members.insert(0, {
                "id": movie_list.owner.id,
                "email": movie_list.owner.email,
                "is_owner": True
            })
        return members

    def remove_member_from_list(self, movie_list: MovieList, user: User) -> MovieList:
        """Remove um usuário da lista de membros."""
        if user in movie_list.members:
            movie_list.members.remove(user)
            self.db.commit()
            self.db.refresh(movie_list)
        return movie_list

    # --- Filmes ---
    def get_movie_by_id(self, movie_id: int) -> Optional[Movie]:
        """Busca um filme pelo id primário."""
        return self.db.query(Movie).filter(Movie.id == movie_id).first()

    def get_movie_in_list_by_tmdb_id(self, list_id: int, tmdb_id: int) -> Optional[Movie]:
        """Verifica se o filme já existe na lista especificada."""
        return self.db.query(Movie).filter(Movie.list_id == list_id, Movie.tmdbId == tmdb_id).first()

    def create_movie(self, list_id: int, movie_data: dict) -> Movie:
        """Cria e persiste um novo filme na lista."""
        new_movie = Movie(**movie_data, list_id=list_id)
        self.db.add(new_movie)
        self.db.commit()
        self.db.refresh(new_movie)
        return new_movie

    def toggle_movie_watched(self, movie: Movie) -> Movie:
        """Alterna o status assistido do filme."""
        movie.watched = not movie.watched
        self.db.commit()
        self.db.refresh(movie)
        return movie

    def delete_movie(self, movie: Movie) -> None:
        """Remove o filme com segurança, desvinculando do histórico de sorteios e limpando comentários."""
        movie_id = movie.id
        # Desvincula do histórico de sorteios para não violar Foreign Key
        self.db.query(DrawHistory).filter(DrawHistory.movie_id == movie_id).update({"movie_id": None}, synchronize_session=False)
        # Remove comentários do filme
        self.db.query(Comment).filter(Comment.movie_id == movie_id).delete(synchronize_session=False)
        self.db.delete(movie)
        self.db.commit()

    # --- Comentários ---
    def add_comment(self, movie_id: int, comment_data: dict) -> Comment:
        """Adiciona um comentário a um filme."""
        new_comment = Comment(
            **comment_data,
            movie_id=movie_id,
            created_at=datetime.now(timezone.utc).isoformat()
        )
        self.db.add(new_comment)
        self.db.commit()
        self.db.refresh(new_comment)
        return new_comment

    # --- Histórico de Sorteios ---
    def add_draw_history(self, list_id: int, history_data: dict) -> DrawHistory:
        """Adiciona um registro de filme sorteado ao histórico."""
        new_entry = DrawHistory(
            **history_data,
            list_id=list_id,
            drawn_at=datetime.now(timezone.utc).isoformat()
        )
        self.db.add(new_entry)
        self.db.commit()
        self.db.refresh(new_entry)
        return new_entry

    def get_draw_history(self, list_id: int, limit: int = 20) -> List[DrawHistory]:
        """Retorna o histórico dos últimos filmes sorteados da lista."""
        return self.db.query(DrawHistory).filter(DrawHistory.list_id == list_id).order_by(DrawHistory.id.desc()).limit(limit).all()

    def cleanup_old_draw_history(self, list_id: int, days: int = 7) -> int:
        """Exclui registros de histórico de sorteios com mais de `days` dias."""
        cutoff_iso = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        deleted_count = self.db.query(DrawHistory).filter(
            DrawHistory.list_id == list_id,
            DrawHistory.drawn_at < cutoff_iso
        ).delete(synchronize_session=False)
        self.db.commit()
        return deleted_count
