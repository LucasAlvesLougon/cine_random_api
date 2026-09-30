def test_comment_identity_cannot_be_supplied_by_client(client, auth_headers):
    list_response = client.post("/lists/", json={"name": "Comentários"}, headers=auth_headers)
    list_code = list_response.json()["code"]
    movie = client.post(
        f"/lists/{list_code}/movies",
        json={"title": "Matrix", "tmdbId": 603},
        headers=auth_headers,
    ).json()

    response = client.post(
        f"/lists/movies/{movie['id']}/comments",
        json={
            "user_id": "999",
            "user_name": "Administrador falso",
            "text": "Comentário",
            "rating": 5,
        },
        headers=auth_headers,
    )

    assert response.status_code == 422


def test_draw_history_identity_cannot_be_supplied_by_client(client, auth_headers):
    client.post("/lists/", json={"name": "Histórico", "code": "HIS001"}, headers=auth_headers)

    response = client.post(
        "/lists/HIS001/history",
        json={
            "movie_title": "Matrix",
            "draw_type": "roulette",
            "drawn_by": "usuário falso",
        },
        headers=auth_headers,
    )

    assert response.status_code == 422


def test_invalid_rating_is_rejected(client, auth_headers):
    list_response = client.post("/lists/", json={"name": "Notas"}, headers=auth_headers)
    list_code = list_response.json()["code"]
    movie = client.post(
        f"/lists/{list_code}/movies",
        json={"title": "Matrix", "tmdbId": 603},
        headers=auth_headers,
    ).json()

    response = client.post(
        f"/lists/movies/{movie['id']}/comments",
        json={"text": "Nota inválida", "rating": 6},
        headers=auth_headers,
    )

    assert response.status_code == 422
