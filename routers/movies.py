from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from database.connection import get_db
from models.models import Movie, MovieList, User
from schemas.schemas import MovieCreate, MovieResponse, MovieListCreate, MovieListResponse
from utils.security import get_current_user

router = APIRouter(prefix="/lists", tags=["Listas de Filmes"])

@router.post("/", response_model=MovieListResponse)
def create_list(lista: MovieListCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Cria uma nova lista vinculada ao usuário logado."""
    db_list = db.query(MovieList).filter(MovieList.code == lista.code).first()
    if db_list:
        raise HTTPException(status_code=400, detail="Código de lista já está em uso.")

    new_list = MovieList(name=lista.name, code=lista.code, owner_id=current_user.id)
    db.add(new_list)
    db.commit()
    db.refresh(new_list)
    return new_list

@router.get("/{list_code}/movies", response_model=List[MovieResponse])
def get_movies(list_code: str, db: Session = Depends(get_db), current_user: User =
Depends(get_current_user)):
    """Retorna todos os filmes de uma lista."""
    db_list = db.query(MovieList).filter(MovieList.code == list_code).first()
    if not db_list:
        raise HTTPException(status_code=404, detail="Lista não encontrada.")

    return db_list.movies

@router.post("/{list_code}/movies", response_model=MovieResponse)
def add_movie(list_code: str, movie: MovieCreate, db: Session = Depends(get_db),
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
    return new_movie

@router.put("/movies/{movie_id}/toggle-watched", response_model=MovieResponse)
def toggle_watched(movie_id: int, db: Session = Depends(get_db), current_user: User =
Depends(get_current_user)):
    """Inverte o status de assistido de um filme específico."""
    movie = db.query(Movie).filter(Movie.id == movie_id).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Filme não encontrado.")

    movie.watched = not movie.watched
    db.commit()
    db.refresh(movie)
    return movie

@router.delete("/movies/{movie_id}")
def delete_movie(movie_id: int, db: Session = Depends(get_db), current_user: User =
Depends(get_current_user)):
    """Remove um filme da lista."""
    movie = db.query(Movie).filter(Movie.id == movie_id).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Filme não encontrado.")

    db.delete(movie)
    db.commit()
    return {"message": "Filme removido com sucesso"}