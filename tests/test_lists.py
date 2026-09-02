def test_create_and_get_my_lists(client, auth_headers):
    # Cria uma lista
    create_res = client.post(
        "/lists/",
        json={"name": "Filmes de Terror", "code": "TERR01"},
        headers=auth_headers
    )
    assert create_res.status_code == 200
    created_data = create_res.json()
    assert created_data["name"] == "Filmes de Terror"
    assert created_data["code"] == "TERR01"

    # Busca listas do usuário
    my_lists_res = client.get("/lists/my", headers=auth_headers)
    assert my_lists_res.status_code == 200
    lists = my_lists_res.json()
    assert len(lists) == 1
    assert lists[0]["code"] == "TERR01"

def test_add_and_toggle_movie(client, auth_headers):
    # Cria lista primeiro
    client.post(
        "/lists/",
        json={"name": "Lista de Ação", "code": "ACT001"},
        headers=auth_headers
    )

    # Adiciona filme
    movie_payload = {
        "title": "Matrix",
        "tmdbId": 603,
        "posterUrl": "https://image.tmdb.org/t/p/w500/matrix.jpg",
        "backdropUrl": "https://image.tmdb.org/t/p/w1280/matrix_backdrop.jpg",
        "synopsis": "Um programador descobre a realidade simulada.",
        "genres": ["Ação", "Ficção Científica"],
        "releaseYear": "1999",
        "runtime": 136,
        "tmdbRating": 8.7,
        "watched": False
    }
    add_res = client.post("/lists/ACT001/movies", json=movie_payload, headers=auth_headers)
    assert add_res.status_code == 200
    movie_data = add_res.json()
    assert movie_data["title"] == "Matrix"
    assert movie_data["watched"] is False
    movie_id = movie_data["id"]

    # Inverte status assistido
    toggle_res = client.put(f"/lists/movies/{movie_id}/toggle-watched", headers=auth_headers)
    assert toggle_res.status_code == 200
    assert toggle_res.json()["watched"] is True

    # Lista filmes
    get_movies_res = client.get("/lists/ACT001/movies", headers=auth_headers)
    assert get_movies_res.status_code == 200
    movies = get_movies_res.json()
    assert len(movies) == 1
    assert movies[0]["watched"] is True

    # Deleta filme
    del_res = client.delete(f"/lists/movies/{movie_id}", headers=auth_headers)
    assert del_res.status_code == 200
    
    # Verifica lista vazia
    movies_after_del = client.get("/lists/ACT001/movies", headers=auth_headers).json()
    assert len(movies_after_del) == 0
