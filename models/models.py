from sqlalchemy import Column, Integer, String, Boolean, Float, ForeignKey, JSON, UniqueConstraint, DateTime
from sqlalchemy.orm import relationship
from database.connection import Base
from datetime import datetime

from sqlalchemy import Table

user_lists_association = Table(
    'user_lists_association',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), index=True),
    Column('list_id', Integer, ForeignKey('lists.id'), index=True),
    UniqueConstraint('user_id', 'list_id', name='uq_user_lists_user_list'),
)
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    google_sub = Column(String, unique=True, index=True, nullable=True)

    lists = relationship("MovieList", back_populates="owner")
    joined_lists = relationship("MovieList", secondary=user_lists_association, back_populates="members")
    password_reset_tokens = relationship("PasswordResetToken", back_populates="user", cascade="all, delete-orphan")


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    token_hash = Column(String, unique=True, nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="password_reset_tokens")

class MovieList(Base):
    __tablename__ = "lists"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    code = Column(String, unique=True, index=True) # Ex: "teste123" que você usou no Front
    owner_id = Column(Integer, ForeignKey("users.id"), index=True)

    owner = relationship("User", back_populates="lists")
    movies = relationship("Movie", back_populates="movie_list", cascade="all, delete-orphan", order_by="Movie.id.desc()")
    members = relationship("User", secondary=user_lists_association, back_populates="joined_lists")
    draw_history = relationship("DrawHistory", back_populates="movie_list", cascade="all, delete-orphan")

class Movie(Base):
    __tablename__ = "movies"
    __table_args__ = (
        UniqueConstraint('list_id', 'tmdbId', name='uq_movies_list_tmdb'),
    )

    id = Column(Integer, primary_key=True, index=True)
    list_id = Column(Integer, ForeignKey("lists.id"), index=True)

    # Dados extraídos do TMDB
    tmdbId = Column(Integer, index=True)
    title = Column(String, nullable=False)
    posterUrl = Column(String)
    backdropUrl = Column(String)
    synopsis = Column(String)
    genres = Column(JSON)
    releaseYear = Column(String)
    runtime = Column(Integer)
    tmdbRating = Column(Float)
    watched = Column(Boolean, default=False)
    watchProviders = Column(JSON)
    trailerKey = Column(String)

    movie_list = relationship("MovieList", back_populates="movies")
    comments = relationship("Comment", back_populates="movie", cascade="all, delete-orphan")
    draw_history = relationship("DrawHistory", back_populates="movie")

class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    movie_id = Column(Integer, ForeignKey("movies.id"), index=True)
    user_id = Column(String)  # Can be email or string id
    user_name = Column(String)
    text = Column(String)
    rating = Column(Integer)
    created_at = Column(String)

    movie = relationship("Movie", back_populates="comments")

class DrawHistory(Base):
    __tablename__ = "draw_history"

    id = Column(Integer, primary_key=True, index=True)
    list_id = Column(Integer, ForeignKey("lists.id"), index=True)
    movie_id = Column(Integer, ForeignKey("movies.id"), nullable=True, index=True)
    movie_title = Column(String, nullable=False)
    movie_poster = Column(String, nullable=True)
    draw_type = Column(String, default="roulette")  # "roulette" ou "match"
    drawn_by = Column(String, nullable=True)
    drawn_at = Column(String)
    archived_at = Column(DateTime(timezone=True), nullable=True)

    movie_list = relationship("MovieList", back_populates="draw_history")
    movie = relationship("Movie", back_populates="draw_history")
