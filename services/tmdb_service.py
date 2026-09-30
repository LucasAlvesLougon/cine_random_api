import httpx
from fastapi import HTTPException, status

from config import settings


class TMDBService:
    async def request(self, path: str, params: dict) -> dict:
        headers = {"accept": "application/json"}
        request_params = dict(params)
        if settings.TMDB_API_READ_ACCESS_TOKEN:
            headers["Authorization"] = f"Bearer {settings.TMDB_API_READ_ACCESS_TOKEN}"
        elif settings.TMDB_API_KEY:
            request_params["api_key"] = settings.TMDB_API_KEY
        else:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Integração com o catálogo indisponível no momento.",
            )

        try:
            async with httpx.AsyncClient(
                base_url=settings.TMDB_BASE_URL,
                timeout=settings.TMDB_TIMEOUT_SECONDS,
            ) as client:
                response = await client.get(path, params=request_params, headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.TimeoutException as exc:
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="O catálogo demorou para responder. Tente novamente.",
            ) from exc
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code in {401, 403}:
                detail = "A integração com o catálogo precisa ser reconfigurada."
            else:
                detail = "O catálogo não está disponível no momento."
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=detail) from exc
        except (httpx.HTTPError, ValueError) as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Não foi possível consultar o catálogo agora.",
            ) from exc


tmdb_service = TMDBService()
