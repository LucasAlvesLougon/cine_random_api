from fastapi import HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional

from repositories.movie_repository import MovieRepository
from models.models import User, MovieList, Movie, Comment, DrawHistory
from schemas.schemas import MovieListCreate, MovieCreate, CommentCreate, DrawHistoryCreate
from sockets import manager
from utils.cache import cache

class MovieService:
    def __init__(self, db: Session):
        self.movie_repo = MovieRepository(db)

    # --- Listas ---
    def get_my_lists(self, current_user: User) -> List[MovieList]:
        """Retorna todas as listas associadas ao usuário com cache in-memory."""
        cache_key = f"user_lists:{current_user.id}"
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        lists = self.movie_repo.get_lists_for_user(current_user)
        cache.set(cache_key, lists, ttl=120)
        return lists

    def join_list(self, list_code: str, current_user: User) -> MovieList:
        """Entra em uma lista existente pelo código e invalida caches."""
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

        updated_list = self.movie_repo.add_member_to_list(db_list, current_user)
        cache.delete(f"members:{list_code}")
        cache.delete_prefix("user_lists:")
        return updated_list

    def create_list(self, lista: MovieListCreate, current_user: User) -> MovieList:
        """Cria uma nova lista para o usuário logado e invalida cache."""
        db_list = self.movie_repo.get_list_by_code(lista.code)
        if db_list:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Código de lista já está em uso."
            )

        new_list = self.movie_repo.create_list(name=lista.name, code=lista.code, owner=current_user)
        cache.delete(f"user_lists:{current_user.id}")
        return new_list

    def update_list(self, list_code: str, list_data: MovieListCreate, current_user: User) -> MovieList:
        """Atualiza o nome da lista com validação de permissão e invalida cache."""
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

        updated_list = self.movie_repo.update_list_name(db_list, list_data.name)
        cache.delete_prefix("user_lists:")
        return updated_list

    def delete_list(self, list_code: str, current_user: User) -> dict:
        """Remove a lista e seus filmes (apenas dono) e limpa os caches."""
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
        cache.delete_prefix(f"movies:{list_code}")
        cache.delete_prefix(f"members:{list_code}")
        cache.delete_prefix(f"history:{list_code}")
        cache.delete_prefix("user_lists:")
        return {"message": "Lista removida com sucesso"}

    def _verify_list_access(self, db_list: MovieList, current_user: User, require_owner: bool = False) -> None:
        """Verifica se o usuário pertence à lista ou é o proprietário (mitigação BOLA/IDOR)."""
        if not db_list:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lista não encontrada."
            )

        is_owner = db_list.owner_id == current_user.id
        is_member = any(m.id == current_user.id for m in db_list.members)

        if require_owner and not is_owner:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Apenas o criador da lista tem permissão para esta ação."
            )

        if not (is_owner or is_member):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Você não possui permissão para acessar ou modificar esta lista."
            )

    def get_list_members(self, list_code: str, current_user: User) -> List[dict]:
        """Retorna todos os participantes da lista com validação de permissão e cache."""
        db_list = self.movie_repo.get_list_by_code(list_code)
        self._verify_list_access(db_list, current_user)

        cache_key = f"members:{list_code}"
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        members = self.movie_repo.get_members_of_list(db_list)
        cache.set(cache_key, members, ttl=180)
        return members

    def remove_list_member(self, list_code: str, user_id: int, current_user: User, background_tasks: BackgroundTasks) -> dict:
        """Remove um participante da lista e invalida cache."""
        db_list = self.movie_repo.get_list_by_code(list_code)
        self._verify_list_access(db_list, current_user)

        if db_list.owner_id != current_user.id and current_user.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Você não tem permissão para remover este participante."
            )
        if user_id == db_list.owner_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="O criador da lista não pode ser removido como participante."
            )

        target_user = next((u for u in db_list.members if u.id == user_id), None)
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Participante não encontrado nesta lista."
            )

        self.movie_repo.remove_member_from_list(db_list, target_user)
        cache.delete(f"members:{list_code}")
        cache.delete_prefix("user_lists:")
        background_tasks.add_task(manager.broadcast_refresh, list_code)
        return {"message": "Participante removido com sucesso"}

    # --- Filmes ---
    def get_movies(self, list_code: str, current_user: User) -> List[Movie]:
        """Retorna todos os filmes de uma lista com validação de permissão e cache in-memory."""
        db_list = self.movie_repo.get_list_by_code(list_code)
        self._verify_list_access(db_list, current_user)

        cache_key = f"movies:{list_code}"
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        movies = db_list.movies
        cache.set(cache_key, movies, ttl=180)
        return movies

    def add_movie(self, list_code: str, movie: MovieCreate, current_user: User, background_tasks: BackgroundTasks) -> Movie:
        """Adiciona um filme validando permissão de lista, duplicidade, invalidando cache e disparando broadcast."""
        db_list = self.movie_repo.get_list_by_code(list_code)
        self._verify_list_access(db_list, current_user)

        db_movie = self.movie_repo.get_movie_in_list_by_tmdb_id(db_list.id, movie.tmdbId)
        if db_movie:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Filme já existe nesta lista."
            )

        new_movie = self.movie_repo.create_movie(db_list.id, movie.model_dump())
        cache.delete(f"movies:{list_code}")
        background_tasks.add_task(manager.broadcast_refresh, list_code)
        return new_movie

    def toggle_watched(self, movie_id: int, current_user: User, background_tasks: BackgroundTasks) -> Movie:
        """Inverte o status assistido do filme com validação de permissão, invalida cache e notifica clientes via WebSocket."""
        movie = self.movie_repo.get_movie_by_id(movie_id)
        if not movie:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Filme não encontrado."
            )

        self._verify_list_access(movie.movie_list, current_user)

        updated_movie = self.movie_repo.toggle_movie_watched(movie)
        list_code = updated_movie.movie_list.code
        cache.delete(f"movies:{list_code}")
        background_tasks.add_task(manager.broadcast_refresh, list_code)
        return updated_movie

    def delete_movie(self, movie_id: int, current_user: User, background_tasks: BackgroundTasks) -> dict:
        """Remove o filme com validação de permissão, invalida cache e notifica clientes via WebSocket."""
        movie = self.movie_repo.get_movie_by_id(movie_id)
        if not movie:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Filme não encontrado."
            )

        self._verify_list_access(movie.movie_list, current_user)

        list_code = movie.movie_list.code
        self.movie_repo.delete_movie(movie)
        cache.delete(f"movies:{list_code}")
        background_tasks.add_task(manager.broadcast_refresh, list_code)
        return {"message": "Filme removido com sucesso"}

    # --- Comentários ---
    def add_comment(self, movie_id: int, comment: CommentCreate, current_user: User, background_tasks: BackgroundTasks) -> Comment:
        """Adiciona comentário com validação de permissão, invalida cache e notifica a sala via WebSocket."""
        movie = self.movie_repo.get_movie_by_id(movie_id)
        if not movie:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Filme não encontrado."
            )

        self._verify_list_access(movie.movie_list, current_user)

        new_comment = self.movie_repo.add_comment(movie_id, comment.model_dump())
        list_code = movie.movie_list.code
        cache.delete(f"movies:{list_code}")
        background_tasks.add_task(manager.broadcast_refresh, list_code)
        return new_comment

    # --- Histórico de Sorteios ---
    def add_draw_history(self, list_code: str, history: DrawHistoryCreate, current_user: User, background_tasks: BackgroundTasks) -> DrawHistory:
        """Registra filme sorteado no histórico com validação de permissão, invalida cache e dispara broadcast."""
        db_list = self.movie_repo.get_list_by_code(list_code)
        self._verify_list_access(db_list, current_user)

        new_entry = self.movie_repo.add_draw_history(db_list.id, history.model_dump())
        cache.delete_prefix(f"history:{list_code}")
        background_tasks.add_task(manager.broadcast_refresh, list_code)
        return new_entry

    def get_draw_history(self, list_code: str, current_user: User, limit: int = 20) -> List[DrawHistory]:
        """Retorna histórico de sorteios da lista com validação de permissão e cache in-memory."""
        db_list = self.movie_repo.get_list_by_code(list_code)
        self._verify_list_access(db_list, current_user)

        cache_key = f"history:{list_code}:{limit}"
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        history = self.movie_repo.get_draw_history(db_list.id, limit=limit)
        cache.set(cache_key, history, ttl=180)
        return history

    def cleanup_old_draw_history(self, list_code: str, current_user: User, days: int = 7, background_tasks: Optional[BackgroundTasks] = None) -> dict:
        """Exclui sorteios com mais de `days` dias com validação de permissão, invalida cache e notifica via WebSocket."""
        db_list = self.movie_repo.get_list_by_code(list_code)
        self._verify_list_access(db_list, current_user)

        deleted_count = self.movie_repo.cleanup_old_draw_history(db_list.id, days=days)
        cache.delete_prefix(f"history:{list_code}")
        if background_tasks:
            background_tasks.add_task(manager.broadcast_refresh, list_code)
        return {
            "deleted_count": deleted_count,
            "message": f"{deleted_count} registros antigos removidos do histórico."
        }

