from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime
from models.models import Movie, MovieList, User, Comment

class MovieRepository:
    def __init__(self, db: Session):
        self.db = db

    # --- Listas ---
    def get_lists_for_user(self, user: User) -> List[MovieList]:
        """Retorna todas as listas que o usuário é dono ou membro."""
        owned = self.db.query(MovieList).filter(MovieList.owner_id == user.id).all()
        joined = user.joined_lists
        all_lists = {lst.id: lst for lst in owned + joined}.values()
        return list(all_lists)

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
        """Exclui todos os filmes vinculados e a lista."""
        self.db.query(Movie).filter(Movie.list_id == movie_list.id).delete()
        self.db.delete(movie_list)
        self.db.commit()

    def add_member_to_list(self, movie_list: MovieList, user: User) -> MovieList:
        """Adiciona um usuário como membro de uma lista."""
        movie_list.members.append(user)
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
        """Remove o filme do banco de dados."""
        self.db.delete(movie)
        self.db.commit()

    # --- Comentários ---
    def add_comment(self, movie_id: int, comment_data: dict) -> Comment:
        """Adiciona um comentário a um filme."""
        new_comment = Comment(
            **comment_data,
            movie_id=movie_id,
            created_at=datetime.utcnow().isoformat()
        )
        self.db.add(new_comment)
        self.db.commit()
        self.db.refresh(new_comment)
        return new_comment
