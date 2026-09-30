def test_tmdb_search_is_proxied_without_exposing_credentials(client, auth_headers, monkeypatch):
    captured = {}

    async def fake_request(path, params):
        captured["path"] = path
        captured["params"] = params
        return {"page": 1, "results": [{"id": 603, "title": "Matrix"}]}

    monkeypatch.setattr("routers.tmdb.tmdb_service.request", fake_request)

    response = client.get(
        "/tmdb/search",
        params={"query": "matrix", "page": 2},
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json()["results"][0]["id"] == 603
    assert captured == {
        "path": "/search/movie",
        "params": {"query": "matrix", "language": "pt-BR", "page": 2},
    }


def test_tmdb_discover_translates_supported_filters(client, auth_headers, monkeypatch):
    captured = {}

    async def fake_request(path, params):
        captured["path"] = path
        captured["params"] = params
        return {"page": params["page"], "results": []}

    monkeypatch.setattr("routers.tmdb.tmdb_service.request", fake_request)

    response = client.get(
        "/tmdb/discover",
        params={"genre_id": 878, "decade": "1980", "page": 3},
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert captured == {
        "path": "/discover/movie",
        "params": {
            "language": "pt-BR",
            "sort_by": "popularity.desc",
            "vote_count.gte": 30,
            "page": 3,
            "with_genres": 878,
            "primary_release_date.gte": "1980-01-01",
            "primary_release_date.lte": "1989-12-31",
        },
    }
