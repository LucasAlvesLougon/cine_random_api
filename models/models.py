from sqlalchemy import Column, Integer, String, Boolean, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship
from database.connection import Base

from sqlalchemy import Table

user_lists_association = Table(
    'user_lists_association',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('list_id', Integer, ForeignKey('lists.id'))
)
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)

    lists = relationship("MovieList", back_populates="owner")
    joined_lists = relationship("MovieList", secondary=user_lists_association, back_populates="members")

class MovieList(Base):
    __tablename__ = "lists"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    code = Column(String, unique=True, index=True) # Ex: "teste123" que vocÃª usou no Front
    owner_id = Column(Integer, ForeignKey("users.id"))

    owner = relationship("User", back_populates="lists")
    movies = relationship("Movie", back_populates="movie_list", order_by="Movie.id")
    members = relationship("User", secondary=user_lists_association, back_populates="joined_lists")

class Movie(Base):
    __tablename__ = "movies"

    id = Column(Integer, primary_key=True, index=True)
    list_id = Column(Integer, ForeignKey("lists.id"))

    # Dados extraÃ­dos do TMDB
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

