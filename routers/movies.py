from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
import asyncio

from database.connection import get_db
from sockets import manager
from models.models import Movie, MovieList, User
from schemas.schemas import MovieCreate, MovieResponse, MovieListCreate, MovieListResponse
from utils.security import get_current_user

router = APIRouter(prefix="/lists", tags=["Listas de Filmes"])

@router.get("/my", response_model=List[MovieListResponse])
def get_my_lists(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Retorna todas as listas que o usuário é dono ou membro."""
    owned = db.query(MovieList).filter(MovieList.owner_id == current_user.id).all()
    joined = current_user.joined_lists
    all_lists = {lst.id: lst for lst in owned + joined}.values()
    return list(all_lists)

@router.post("/join/{list_code}", response_model=MovieListResponse)
def join_list(list_code: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Entra em uma lista existente usando o código."""
    db_list = db.query(MovieList).filter(MovieList.code == list_code).first()
    if not db_list:
        raise HTTPException(status_code=404, detail="Código de lista inválido.")
    if current_user in db_list.members or db_list.owner_id == current_user.id:
        raise HTTPException(status_code=400, detail="Você já está nesta lista.")
    
    db_list.members.append(current_user)
    db.commit()
    return db_list

@router.post("/", response_model=MovieListResponse)
def create_list(lista: MovieListCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Cria uma nova lista vinculada ao usuário logado."""
    db_list = db.query(MovieList).filter(MovieList.code == lista.code).first()
    if db_list:
        raise HTTPException(status_code=400, detail="Código de lista já está em uso.")

    new_list = MovieList(name=lista.name, code=lista.code, owner_id=current_user.id)
    new_list.members.append(current_user)
    db.add(new_list)
    db.commit()
    db.refresh(new_list)
    return new_list

@router.put("/{list_code}", response_model=MovieListResponse)
def update_list(list_code: str, list_data: MovieListCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Atualiza o nome de uma lista."""
    db_list = db.query(MovieList).filter(MovieList.code == list_code).first()
    if not db_list:
        raise HTTPException(status_code=404, detail="Lista não encontrada.")
    if db_list.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Somente o dono pode alterar o nome da lista.")
    db_list.name = list_data.name
    db.commit()
    db.refresh(db_list)
    return db_list

@router.delete("/{list_code}")
def delete_list(list_code: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Remove uma lista (apenas o dono pode excluir)."""
    db_list = db.query(MovieList).filter(MovieList.code == list_code).first()
    if not db_list:
        raise HTTPException(status_code=404, detail="Lista não encontrada.")
    if db_list.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Somente o dono pode excluir a lista.")
    
    db.query(Movie).filter(Movie.list_id == db_list.id).delete()
    db.delete(db_list)
    db.commit()
    return {"message": "Lista removida com sucesso"}

@router.get("/{list_code}/movies", response_model=List[MovieResponse])
def get_movies(list_code: str, db: Session = Depends(get_db), current_user: User =
Depends(get_current_user)):
    """Retorna todos os filmes de uma lista."""
    db_list = db.query(MovieList).filter(MovieList.code == list_code).first()
    if not db_list:
        raise HTTPException(status_code=404, detail="Lista não encontrada.")

    return db_list.movies

@router.post("/{list_code}/movies", response_model=MovieResponse)
def add_movie(list_code: str, movie: MovieCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db),
current_user: User = Depends(get_current_user)):
    """Adiciona um filme a uma lista (evitando duplicatas)."""
    db_list = db.query(MovieList).filter(MovieList.code == list_code).first()
    if not db_list:
        raise HTTPException(status_code=404, detail="Lista não encontrada.")

    db_movie = db.query(Movie).filter(Movie.list_id == db_list.id, Movie.tmdbId == movie.
tmdbId).first()
    if db_movie:
        raise HTTPException(status_code=400, detail="Filme já existe nesta lista.")

    new_movie = Movie(**movie.model_dump(), list_id=db_list.id)
    db.add(new_movie)
    db.commit()
    db.refresh(new_movie)
    background_tasks.add_task(manager.broadcast_refresh, list_code)
    return new_movie

@router.put("/movies/{movie_id}/toggle-watched", response_model=MovieResponse)
def toggle_watched(movie_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db), current_user: User =
Depends(get_current_user)):
    """Inverte o status de assistido de um filme específico."""
    movie = db.query(Movie).filter(Movie.id == movie_id).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Filme não encontrado.")

    movie.watched = not movie.watched
    db.commit()
    db.refresh(movie)
    list_code = movie.movie_list.code
    background_tasks.add_task(manager.broadcast_refresh, list_code)
    return movie

@router.delete("/movies/{movie_id}")
def delete_movie(movie_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db), current_user: User =
Depends(get_current_user)):
    """Remove um filme da lista."""
    movie = db.query(Movie).filter(Movie.id == movie_id).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Filme não encontrado.")

    list_code = movie.movie_list.code
    db.delete(movie)
    db.commit()
    background_tasks.add_task(manager.broadcast_refresh, list_code)
    return {"message": "Filme removido com sucesso"}
@router.websocket('/ws/{list_code}')
async def websocket_endpoint(websocket: WebSocket, list_code: str):
    await manager.connect(websocket, list_code)
    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, list_code)
