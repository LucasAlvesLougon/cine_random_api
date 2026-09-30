from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional, Dict, Any, Literal

# --- USERS & AUTH ---
class UserBase(BaseModel):
    email: str

class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)

class UserResponse(UserBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    email: Optional[str] = None
    user_id: Optional[int] = None

class GoogleAuthRequest(BaseModel):
    credential: str
    model_config = ConfigDict(extra="forbid")


class GoogleLinkConfirmationRequest(BaseModel):
    credential: str
    password: str
    model_config = ConfigDict(extra="forbid")


class GoogleLinkResponse(BaseModel):
    detail: str
    email: str
    user_id: int


class DemoAuthRequest(BaseModel):
    email: str
    model_config = ConfigDict(extra="forbid")


class PasswordResetRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    model_config = ConfigDict(extra="forbid")


class PasswordResetConfirm(BaseModel):
    token: str = Field(min_length=20, max_length=200)
    new_password: str = Field(min_length=8, max_length=128)
    model_config = ConfigDict(extra="forbid")


class PasswordResetResponse(BaseModel):
    detail: str


# --- LISTAS ---
class MovieListBase(BaseModel):
    name: str = Field(min_length=1, max_length=120)

class MovieListCreate(MovieListBase):
    code: Optional[str] = Field(default=None, min_length=4, max_length=32, pattern=r"^[A-Za-z0-9_-]+$")

class MovieListUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=120)

class MovieListResponse(BaseModel):
    name: str
    code: str
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
    title: str = Field(min_length=1, max_length=300)
    posterUrl: Optional[str] = Field(default=None, max_length=1000)
    backdropUrl: Optional[str] = Field(default=None, max_length=1000)
    synopsis: Optional[str] = Field(default=None, max_length=5000)
    genres: Optional[List[str]] = Field(default_factory=list)
    releaseYear: Optional[str] = Field(default=None, max_length=10)
    runtime: Optional[int] = Field(default=None, ge=0, le=1000)
    tmdbRating: Optional[float] = Field(default=None, ge=0, le=10)
    watched: bool = False
    watchProviders: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    trailerKey: Optional[str] = Field(default=None, max_length=200)

class MovieCreate(MovieBase):
    pass

class CommentCreate(BaseModel):
    text: str = Field(min_length=1, max_length=2000)
    rating: int = Field(ge=1, le=5)
    model_config = ConfigDict(extra="forbid")

class CommentResponse(CommentCreate):
    id: int
    movie_id: int
    user_id: str
    user_name: str
    created_at: str
    model_config = ConfigDict(from_attributes=True)

class MovieResponse(MovieBase):
    id: int
    list_id: int
    comments: List[CommentResponse] = []
    model_config = ConfigDict(from_attributes=True)


class MoviePageResponse(BaseModel):
    items: List[MovieResponse]
    total: int
    page: int
    page_size: int
    has_next: bool

# --- HISTÓRICO DE SORTEIOS ---
class DrawHistoryCreate(BaseModel):
    movie_id: Optional[int] = None
    movie_title: str = Field(min_length=1, max_length=300)
    movie_poster: Optional[str] = Field(default=None, max_length=1000)
    draw_type: Literal["roulette", "discovery", "match"] = "roulette"
    model_config = ConfigDict(extra="forbid")

class DrawHistoryResponse(DrawHistoryCreate):
    id: int
    list_id: int
    drawn_by: Optional[str] = None
    drawn_at: str
    model_config = ConfigDict(from_attributes=True)

class WebSocketTicketResponse(BaseModel):
    ticket: str
    expires_in: int

class InviteResponse(BaseModel):
    code: str
    join_url: str
