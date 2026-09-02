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

def test_add_comment_and_rating(client, auth_headers):
    # Cria lista e adiciona filme
    client.post("/lists/", json={"name": "Cinema Clube", "code": "CLB01"}, headers=auth_headers)
    movie_res = client.post(
        "/lists/CLB01/movies",
        json={"title": "Inception", "tmdbId": 27205, "releaseYear": "2010"},
        headers=auth_headers
    )
    movie_id = movie_res.json()["id"]

    # Adiciona comentário com nota
    comment_payload = {
        "user_id": "test@example.com",
        "user_name": "Test User",
        "text": "Obra de arte do Christopher Nolan!",
        "rating": 5
    }
    comment_res = client.post(f"/lists/movies/{movie_id}/comments", json=comment_payload, headers=auth_headers)
    assert comment_res.status_code == 200
    comment_data = comment_res.json()
    assert comment_data["text"] == "Obra de arte do Christopher Nolan!"
    assert comment_data["rating"] == 5

    # Verifica se o filme na lista traz o comentário
    movies_res = client.get("/lists/CLB01/movies", headers=auth_headers)
    assert movies_res.status_code == 200
    movie = movies_res.json()[0]
    assert len(movie["comments"]) == 1
    assert movie["comments"][0]["rating"] == 5

def test_add_and_get_draw_history(client, auth_headers):
    # Cria lista
    client.post("/lists/", json={"name": "Sessão Pipoca", "code": "PIP01"}, headers=auth_headers)

    # Registra sorteio no histórico
    history_payload = {
        "movie_title": "Interestelar",
        "movie_poster": "https://image.tmdb.org/t/p/w500/interstellar.jpg",
        "draw_type": "roulette",
        "drawn_by": "test@example.com"
    }
    post_res = client.post("/lists/PIP01/history", json=history_payload, headers=auth_headers)
    assert post_res.status_code == 200
    history_data = post_res.json()
    assert history_data["movie_title"] == "Interestelar"
    assert history_data["draw_type"] == "roulette"
    assert "drawn_at" in history_data

    # Consulta histórico
    get_res = client.get("/lists/PIP01/history", headers=auth_headers)
    assert get_res.status_code == 200
    history_list = get_res.json()
    assert len(history_list) == 1
    assert history_list[0]["movie_title"] == "Interestelar"
