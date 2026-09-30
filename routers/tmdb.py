from fastapi import APIRouter, Depends, Query

from models.models import User
from services.tmdb_service import tmdb_service
from utils.rate_limit import rate_limit
from utils.security import get_current_user


router = APIRouter(prefix="/tmdb", tags=["TMDB"])
_catalog_limit = Depends(rate_limit(limit=60, window_seconds=60))


@router.get("/search", dependencies=[_catalog_limit])
async def search_movies(
    query: str = Query(min_length=2, max_length=100),
    page: int = Query(1, ge=1, le=500),
    language: str = Query("pt-BR", pattern=r"^[a-z]{2}(?:-[A-Z]{2})?$"),
    _: User = Depends(get_current_user),
):
    return await tmdb_service.request("/search/movie", {
        "query": query.strip(),
        "language": language,
        "page": page,
    })


@router.get("/movie/{tmdb_id}", dependencies=[_catalog_limit])
async def movie_details(
    tmdb_id: int,
    language: str = Query("pt-BR", pattern=r"^[a-z]{2}(?:-[A-Z]{2})?$"),
    _: User = Depends(get_current_user),
):
    return await tmdb_service.request(f"/movie/{tmdb_id}", {
        "language": language,
        "append_to_response": "watch/providers,videos,credits",
        "include_video_language": "pt-BR,en,null",
    })


@router.get("/discover", dependencies=[_catalog_limit])
async def discover_movies(
    genre_id: int | None = Query(None, ge=1, le=10000),
    decade: str | None = Query(None, pattern=r"^(?:recent|19[0-9]{2}|20[0-9]{2})$"),
    page: int = Query(1, ge=1, le=500),
    _: User = Depends(get_current_user),
):
    params = {
        "language": "pt-BR",
        "sort_by": "popularity.desc",
        "vote_count.gte": 30,
        "page": page,
    }
    if genre_id:
        params["with_genres"] = genre_id
    if decade == "recent":
        params["primary_release_date.gte"] = "2020-01-01"
    elif decade:
        params["primary_release_date.gte"] = f"{decade}-01-01"
        params["primary_release_date.lte"] = f"{int(decade) + 9}-12-31"
    return await tmdb_service.request("/discover/movie", params)


@router.get("/popular", dependencies=[_catalog_limit])
async def popular_movies(
    page: int = Query(1, ge=1, le=500),
    _: User = Depends(get_current_user),
):
    return await tmdb_service.request("/movie/popular", {"language": "pt-BR", "page": page})
