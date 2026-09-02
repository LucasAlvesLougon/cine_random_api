from fastapi import HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List

from repositories.movie_repository import MovieRepository
from models.models import User, MovieList, Movie, Comment, DrawHistory
from schemas.schemas import MovieListCreate, MovieCreate, CommentCreate, DrawHistoryCreate
from sockets import manager

class MovieService:
    def __init__(self, db: Session):
        self.movie_repo = MovieRepository(db)

    # --- Listas ---
    def get_my_lists(self, current_user: User) -> List[MovieList]:
        """Retorna todas as listas associadas ao usuário."""
        return self.movie_repo.get_lists_for_user(current_user)

    def join_list(self, list_code: str, current_user: User) -> MovieList:
        """Entra em uma lista existente pelo código."""
        db_list = self.movie_repo.get_list_by_code(list_code)
        if not db_list:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Código de lista inválido."
            )
        if current_user in db_list.members or db_list.owner_id == current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Você já está nesta lista."
            )

        return self.movie_repo.add_member_to_list(db_list, current_user)

    def create_list(self, lista: MovieListCreate, current_user: User) -> MovieList:
        """Cria uma nova lista para o usuário logado."""
        db_list = self.movie_repo.get_list_by_code(lista.code)
        if db_list:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Código de lista já está em uso."
            )

        return self.movie_repo.create_list(name=lista.name, code=lista.code, owner=current_user)

    def update_list(self, list_code: str, list_data: MovieListCreate, current_user: User) -> MovieList:
        """Atualiza o nome da lista com validação de permissão."""
        db_list = self.movie_repo.get_list_by_code(list_code)
        if not db_list:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lista não encontrada."
            )
        if db_list.owner_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Somente o dono pode alterar o nome da lista."
            )

        return self.movie_repo.update_list_name(db_list, list_data.name)

    def delete_list(self, list_code: str, current_user: User) -> dict:
        """Remove a lista e seus filmes (apenas dono)."""
        db_list = self.movie_repo.get_list_by_code(list_code)
        if not db_list:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lista não encontrada."
            )
        if db_list.owner_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Somente o dono pode excluir a lista."
            )

        self.movie_repo.delete_list(db_list)
        return {"message": "Lista removida com sucesso"}

    def get_list_members(self, list_code: str) -> List[dict]:
        """Retorna todos os participantes da lista."""
        db_list = self.movie_repo.get_list_by_code(list_code)
        if not db_list:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lista não encontrada."
            )
        return self.movie_repo.get_members_of_list(db_list)

    # --- Filmes ---
    def get_movies(self, list_code: str) -> List[Movie]:
        """Retorna todos os filmes de uma lista."""
        db_list = self.movie_repo.get_list_by_code(list_code)
        if not db_list:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lista não encontrada."
            )
        return db_list.movies

    def add_movie(self, list_code: str, movie: MovieCreate, background_tasks: BackgroundTasks) -> Movie:
        """Adiciona um filme validando duplicidade e disparando broadcast."""
        db_list = self.movie_repo.get_list_by_code(list_code)
        if not db_list:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lista não encontrada."
            )

        db_movie = self.movie_repo.get_movie_in_list_by_tmdb_id(db_list.id, movie.tmdbId)
        if db_movie:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Filme já existe nesta lista."
            )

        new_movie = self.movie_repo.create_movie(db_list.id, movie.model_dump())
        background_tasks.add_task(manager.broadcast_refresh, list_code)
        return new_movie

    def toggle_watched(self, movie_id: int, background_tasks: BackgroundTasks) -> Movie:
        """Inverte o status assistido do filme e notifica clientes via WebSocket."""
        movie = self.movie_repo.get_movie_by_id(movie_id)
        if not movie:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Filme não encontrado."
            )

        updated_movie = self.movie_repo.toggle_movie_watched(movie)
        list_code = updated_movie.movie_list.code
        background_tasks.add_task(manager.broadcast_refresh, list_code)
        return updated_movie

    def delete_movie(self, movie_id: int, background_tasks: BackgroundTasks) -> dict:
        """Remove o filme e notifica clientes via WebSocket."""
        movie = self.movie_repo.get_movie_by_id(movie_id)
        if not movie:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Filme não encontrado."
            )

        list_code = movie.movie_list.code
        self.movie_repo.delete_movie(movie)
        background_tasks.add_task(manager.broadcast_refresh, list_code)
        return {"message": "Filme removido com sucesso"}

    # --- Comentários ---
    def add_comment(self, movie_id: int, comment: CommentCreate, background_tasks: BackgroundTasks) -> Comment:
        """Adiciona comentário e notifica a sala via WebSocket."""
        movie = self.movie_repo.get_movie_by_id(movie_id)
        if not movie:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Filme não encontrado."
            )

        new_comment = self.movie_repo.add_comment(movie_id, comment.model_dump())
        list_code = movie.movie_list.code
        background_tasks.add_task(manager.broadcast_refresh, list_code)
        return new_comment

    # --- Histórico de Sorteios ---
    def add_draw_history(self, list_code: str, history: DrawHistoryCreate, background_tasks: BackgroundTasks) -> DrawHistory:
        """Registra filme sorteado no histórico e dispara broadcast."""
        db_list = self.movie_repo.get_list_by_code(list_code)
        if not db_list:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lista não encontrada."
            )

        new_entry = self.movie_repo.add_draw_history(db_list.id, history.model_dump())
        background_tasks.add_task(manager.broadcast_refresh, list_code)
        return new_entry

    def get_draw_history(self, list_code: str, limit: int = 20) -> List[DrawHistory]:
        """Retorna histórico de sorteios da lista."""
        db_list = self.movie_repo.get_list_by_code(list_code)
        if not db_list:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lista não encontrada."
            )

        return self.movie_repo.get_draw_history(db_list.id, limit=limit)
