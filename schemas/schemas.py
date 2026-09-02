from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Dict, Any

# --- USERS & AUTH ---
class UserBase(BaseModel):
    email: str

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    email: Optional[str] = None
    user_id: Optional[int] = None

class GoogleAuthRequest(BaseModel):
    idToken: str


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

class MemberResponse(BaseModel):
    id: int
    email: str
    is_owner: bool
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

class CommentBase(BaseModel):
    user_id: str
    user_name: str
    text: str
    rating: int

class CommentCreate(CommentBase):
    pass

class CommentResponse(CommentBase):
    id: int
    movie_id: int
    created_at: str
    model_config = ConfigDict(from_attributes=True)

class MovieResponse(MovieBase):
    id: int
    list_id: int
    comments: List[CommentResponse] = []
    model_config = ConfigDict(from_attributes=True)

# --- HISTÓRICO DE SORTEIOS ---
class DrawHistoryBase(BaseModel):
    movie_id: Optional[int] = None
    movie_title: str
    movie_poster: Optional[str] = None
    draw_type: str = "roulette"
    drawn_by: Optional[str] = None

class DrawHistoryCreate(DrawHistoryBase):
    pass

class DrawHistoryResponse(DrawHistoryBase):
    id: int
    list_id: int
    drawn_at: str
    model_config = ConfigDict(from_attributes=True)
