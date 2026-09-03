from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, BackgroundTasks, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from database.connection import get_db
from sockets import manager
from models.models import User, MovieList
from schemas.schemas import (
    MovieCreate, MovieResponse, MovieListCreate,
    MovieListResponse, CommentCreate, CommentResponse,
    DrawHistoryCreate, DrawHistoryResponse, MemberResponse
)
from services.movie_service import MovieService
from utils.security import get_current_user, decode_token

router = APIRouter(prefix="/lists", tags=["Listas de Filmes"])

@router.get("/my", response_model=List[MovieListResponse])
def get_my_lists(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Retorna todas as listas que o usuário é dono ou membro."""
    service = MovieService(db)
    return service.get_my_lists(current_user)

@router.post("/join/{list_code}", response_model=MovieListResponse)
def join_list(list_code: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Entra em uma lista existente usando o código."""
    service = MovieService(db)
    return service.join_list(list_code, current_user)

@router.post("/", response_model=MovieListResponse)
def create_list(lista: MovieListCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Cria uma nova lista vinculada ao usuário logado."""
    service = MovieService(db)
    return service.create_list(lista, current_user)

@router.put("/{list_code}", response_model=MovieListResponse)
def update_list(list_code: str, list_data: MovieListCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Atualiza o nome de uma lista."""
    service = MovieService(db)
    return service.update_list(list_code, list_data, current_user)

@router.delete("/{list_code}")
def delete_list(list_code: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Remove uma lista (apenas o dono pode excluir)."""
    service = MovieService(db)
    return service.delete_list(list_code, current_user)

@router.get("/{list_code}/members", response_model=List[MemberResponse])
def get_list_members(list_code: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Retorna todos os participantes de uma lista com identificação do dono."""
    service = MovieService(db)
    return service.get_list_members(list_code, current_user)

@router.delete("/{list_code}/members/{user_id}")
def remove_list_member(list_code: str, user_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Remove um participante da lista (apenas dono ou o próprio membro)."""
    service = MovieService(db)
    return service.remove_list_member(list_code, user_id, current_user, background_tasks)

@router.get("/{list_code}/movies", response_model=List[MovieResponse])
def get_movies(list_code: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Retorna todos os filmes de uma lista."""
    service = MovieService(db)
    return service.get_movies(list_code, current_user)

@router.post("/{list_code}/movies", response_model=MovieResponse)
def add_movie(list_code: str, movie: MovieCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Adiciona um filme a uma lista (evitando duplicatas)."""
    service = MovieService(db)
    return service.add_movie(list_code, movie, current_user, background_tasks)

@router.put("/movies/{movie_id}/toggle-watched", response_model=MovieResponse)
def toggle_watched(movie_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Inverte o status de assistido de um filme específico."""
    service = MovieService(db)
    return service.toggle_watched(movie_id, current_user, background_tasks)

@router.delete("/movies/{movie_id}")
def delete_movie(movie_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Remove um filme da lista."""
    service = MovieService(db)
    return service.delete_movie(movie_id, current_user, background_tasks)

@router.post("/movies/{movie_id}/comments", response_model=CommentResponse)
def add_comment(movie_id: int, comment: CommentCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Adiciona um comentário ao filme."""
    service = MovieService(db)
    return service.add_comment(movie_id, comment, current_user, background_tasks)

@router.post("/{list_code}/history", response_model=DrawHistoryResponse)
def add_draw_history(list_code: str, history: DrawHistoryCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Registra um filme sorteado no histórico da lista."""
    service = MovieService(db)
    return service.add_draw_history(list_code, history, current_user, background_tasks)

@router.get("/{list_code}/history", response_model=List[DrawHistoryResponse])
def get_draw_history(list_code: str, limit: int = 20, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Retorna os últimos filmes sorteados na lista."""
    service = MovieService(db)
    return service.get_draw_history(list_code, current_user, limit=limit)

@router.delete("/{list_code}/history/cleanup")
def cleanup_draw_history(list_code: str, days: int = 7, background_tasks: BackgroundTasks = BackgroundTasks(), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Remove registros de sorteios mais antigos que 'days' dias (padrão: 7 dias)."""
    service = MovieService(db)
    return service.cleanup_old_draw_history(list_code, current_user, days=days, background_tasks=background_tasks)

@router.websocket('/ws/{list_code}')
async def websocket_endpoint(
    websocket: WebSocket,
    list_code: str,
    token: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    email = decode_token(token)
    if not email:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    user = db.query(User).filter(User.email == email).first()
    if not user:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    db_list = db.query(MovieList).filter(MovieList.code == list_code).first()
    if not db_list or (db_list.owner_id != user.id and not any(m.id == user.id for m in db_list.members)):
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await manager.connect(websocket, list_code)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, list_code)


