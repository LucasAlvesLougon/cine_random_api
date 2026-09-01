from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Dict, Any

# --- USERS ---
class UserBase(BaseModel):
    email: str

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

# --- LISTAS ---
class MovieListBase(BaseModel):
    name: str
    code: str

class MovieListCreate(MovieListBase):
    pass

class MovieListResponse(MovieListBase):
    id: int
    owner_id: Optional[int] = None
    model_config = ConfigDict(from_attributes=True)

# --- FILMES ---
class MovieBase(BaseModel):
    tmdbId: int
    title: str
    posterUrl: Optional[str] = None
    backdropUrl: Optional[str] = None
    synopsis: Optional[str] = None
    genres: Optional[List[str]] = []
    releaseYear: Optional[str] = None
    runtime: Optional[int] = None
    tmdbRating: Optional[float] = None
    watched: bool = False
    watchProviders: Optional[List[Dict[str, Any]]] = []
    trailerKey: Optional[str] = None

class MovieCreate(MovieBase):
    pass

class MovieResponse(MovieBase):
    id: int
    list_id: int
    model_config = ConfigDict(from_attributes=True)
