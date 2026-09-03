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

def test_get_list_members(client, auth_headers):
    # Cria lista
    client.post("/lists/", json={"name": "Amigos do Cinema", "code": "MBR01"}, headers=auth_headers)

    # Consulta membros da lista
    members_res = client.get("/lists/MBR01/members", headers=auth_headers)
    assert members_res.status_code == 200
    members = members_res.json()
    assert len(members) >= 1
    assert members[0]["email"] == "tester@example.com"
    assert members[0]["is_owner"] is True

def test_remove_list_member(client, auth_headers):
    # Cria usuário 2
    client.post("/auth/signup", json={"email": "member2@example.com", "password": "password123"})
    login_res = client.post(
        "/auth/login",
        data={"username": "member2@example.com", "password": "password123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    token2 = login_res.json()["access_token"]
    headers2 = {"Authorization": f"Bearer {token2}"}

    # Cria lista com usuário 1
    client.post("/lists/", json={"name": "Clube VIP", "code": "VIP01"}, headers=auth_headers)

    # Usuário 2 entra na lista
    join_res = client.post("/lists/join/VIP01", headers=headers2)
    assert join_res.status_code == 200

    # Verifica se há 2 membros
    members_res = client.get("/lists/VIP01/members", headers=auth_headers)
    assert len(members_res.json()) == 2
    member2_id = next(m["id"] for m in members_res.json() if m["email"] == "member2@example.com")

    # Usuário 1 (dono) remove usuário 2
    del_res = client.delete(f"/lists/VIP01/members/{member2_id}", headers=auth_headers)
    assert del_res.status_code == 200

    # Verifica se agora só restou 1 membro
    members_after = client.get("/lists/VIP01/members", headers=auth_headers)
    assert len(members_after.json()) == 1

def test_cleanup_old_draw_history(client, auth_headers, db_session):
    from datetime import datetime, timezone, timedelta
    from models.models import DrawHistory, MovieList

    # Cria lista
    client.post("/lists/", json={"name": "Histórico Antigo", "code": "CLN01"}, headers=auth_headers)
    db_list = db_session.query(MovieList).filter(MovieList.code == "CLN01").first()

    # Cria 1 registro recente (hoje) e 1 registro antigo (10 dias atrás)
    old_date = (datetime.now(timezone.utc) - timedelta(days=10)).isoformat()
    recent_date = datetime.now(timezone.utc).isoformat()

    old_entry = DrawHistory(
        list_id=db_list.id,
        movie_title="Matrix Antigo",
        draw_type="roulette",
        drawn_at=old_date
    )
    recent_entry = DrawHistory(
        list_id=db_list.id,
        movie_title="Interestelar Recente",
        draw_type="roulette",
        drawn_at=recent_date
    )
    db_session.add_all([old_entry, recent_entry])
    db_session.commit()

    # Confirma que há 2 itens no histórico
    get_res = client.get("/lists/CLN01/history", headers=auth_headers)
    assert len(get_res.json()) == 2

    # Executa limpeza de registros com mais de 7 dias
    clean_res = client.delete("/lists/CLN01/history/cleanup?days=7", headers=auth_headers)
    assert clean_res.status_code == 200
    assert clean_res.json()["deleted_count"] == 1

    # Confirma que só restou o registro recente
    get_after = client.get("/lists/CLN01/history", headers=auth_headers)
    history_after = get_after.json()
    assert len(history_after) == 1
    assert history_after[0]["movie_title"] == "Interestelar Recente"

def test_bola_unauthorized_movie_access_and_modification(client, auth_headers):
    # Usuário 1 (auth_headers) cria uma lista e adiciona um filme
    client.post("/lists/", json={"name": "Lista Privada de A", "code": "PRIV01"}, headers=auth_headers)
    add_res = client.post("/lists/PRIV01/movies", json={"title": "Matrix", "tmdbId": 603}, headers=auth_headers)
    assert add_res.status_code == 200
    movie_id = add_res.json()["id"]

    # Usuário 2 se cadastra e loga
    client.post("/auth/signup", json={"email": "attacker@example.com", "password": "password123"})
    login_res = client.post(
        "/auth/login",
        data={"username": "attacker@example.com", "password": "password123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    token2 = login_res.json()["access_token"]
    attacker_headers = {"Authorization": f"Bearer {token2}"}

    # 1. Atacante tenta listar filmes da lista privada -> 403 Forbidden
    res_get = client.get("/lists/PRIV01/movies", headers=attacker_headers)
    assert res_get.status_code == 403

    # 2. Atacante tenta adicionar filme na lista de A -> 403 Forbidden
    res_add = client.post("/lists/PRIV01/movies", json={"title": "Invasor", "tmdbId": 999}, headers=attacker_headers)
    assert res_add.status_code == 403

    # 3. Atacante tenta marcar o filme de A como assistido -> 403 Forbidden
    res_toggle = client.put(f"/lists/movies/{movie_id}/toggle-watched", headers=attacker_headers)
    assert res_toggle.status_code == 403

    # 4. Atacante tenta deletar o filme de A -> 403 Forbidden
    res_del = client.delete(f"/lists/movies/{movie_id}", headers=attacker_headers)
    assert res_del.status_code == 403

    # 5. Atacante tenta listar membros da lista de A -> 403 Forbidden
    res_members = client.get("/lists/PRIV01/members", headers=attacker_headers)
    assert res_members.status_code == 403

    # 6. Atacante tenta ver o histórico da lista de A -> 403 Forbidden
    res_history = client.get("/lists/PRIV01/history", headers=attacker_headers)
    assert res_history.status_code == 403

def test_websocket_authentication_and_authorization(client, auth_headers):
    # Usuário 1 cria uma lista
    client.post("/lists/", json={"name": "Lista WebSocket", "code": "WS001"}, headers=auth_headers)
    token1 = auth_headers["Authorization"].split(" ")[1]

    # Cria Usuário 2 (não membro)
    client.post("/auth/signup", json={"email": "ws_stranger@example.com", "password": "password123"})
    login_res = client.post(
        "/auth/login",
        data={"username": "ws_stranger@example.com", "password": "password123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    token2 = login_res.json()["access_token"]

    # Conexão sem token -> deve falhar
    import pytest
    from starlette.websockets import WebSocketDisconnect

    with pytest.raises(Exception):
        with client.websocket_connect("/lists/ws/WS001") as ws:
            pass

    # Conexão com token de usuário que não é membro -> deve falhar
    with pytest.raises(Exception):
        with client.websocket_connect(f"/lists/ws/WS001?token={token2}") as ws:
            pass

    # Conexão com token válido do dono -> deve conectar com sucesso
    with client.websocket_connect(f"/lists/ws/WS001?token={token1}") as ws:
        assert ws is not None

def test_delete_list_with_all_relationships(client, auth_headers):
    # 1. Cria lista
    res_list = client.post("/lists/", json={"name": "Lista Completa Para Deletar", "code": "DELFULL01"}, headers=auth_headers)
    assert res_list.status_code == 200

    # 2. Adiciona participante/membro
    client.post("/auth/signup", json={"email": "member_del@example.com", "password": "password123"})
    login_member = client.post(
        "/auth/login",
        data={"username": "member_del@example.com", "password": "password123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    member_token = login_member.json()["access_token"]
    member_headers = {"Authorization": f"Bearer {member_token}"}
    client.post("/lists/join/DELFULL01", headers=member_headers)

    # 3. Adiciona filme
    res_movie = client.post(
        "/lists/DELFULL01/movies",
        json={"title": "O Poderoso Chefão", "tmdbId": 238, "releaseYear": "1972"},
        headers=auth_headers
    )
    assert res_movie.status_code == 200
    movie_id = res_movie.json()["id"]

    # 4. Adiciona comentário no filme
    res_comm = client.post(
        f"/lists/movies/{movie_id}/comments",
        json={"user_id": "1", "user_name": "Tester", "text": "Obra de arte absoluta!", "rating": 5},
        headers=auth_headers
    )
    assert res_comm.status_code == 200

    # 5. Registra sorteio no histórico
    res_hist = client.post(
        "/lists/DELFULL01/history",
        json={
            "movie_id": movie_id,
            "movie_title": "O Poderoso Chefão",
            "draw_type": "roulette"
        },
        headers=auth_headers
    )
    assert res_hist.status_code == 200

    # 6. Deleta a lista inteira (dono) -> deve deletar sem erro 500
    del_list_res = client.delete("/lists/DELFULL01", headers=auth_headers)
    assert del_list_res.status_code == 200
    assert del_list_res.json()["message"] == "Lista removida com sucesso"

    # 7. Verifica que a lista não existe mais
    check_res = client.get("/lists/DELFULL01/movies", headers=auth_headers)
    assert check_res.status_code == 404


