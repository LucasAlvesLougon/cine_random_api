def create_list(client, headers, name):
    response = client.post("/lists/", json={"name": name}, headers=headers)
    assert response.status_code == 200
    return response.json()


def test_create_and_get_my_lists(client, auth_headers):
    # Cria uma lista
    created_data = create_list(client, auth_headers, "Filmes de Terror")
    assert created_data["name"] == "Filmes de Terror"
    assert len(created_data["code"]) == 8

    # Busca listas do usuário
    my_lists_res = client.get("/lists/my", headers=auth_headers)
    assert my_lists_res.status_code == 200
    lists = my_lists_res.json()
    assert len(lists) == 1
    assert lists[0]["code"] == created_data["code"]


def test_invite_is_generated_by_server_and_can_be_shared(client, auth_headers):
    created = client.post(
        "/lists/",
        json={"name": "Convite Seguro", "code": "CLIENT_CODE_SHOULD_BE_IGNORED"},
        headers=auth_headers,
    )
    assert created.status_code == 200
    list_data = created.json()

    assert len(list_data["code"]) == 8
    assert list_data["code"] != "CLIENT_CODE_SHOULD_BE_IGNORED"

    invite = client.get(f"/lists/{list_data['code']}/invite", headers=auth_headers)
    assert invite.status_code == 200
    assert invite.json() == {
        "code": list_data["code"],
        "join_url": f"http://localhost:5173/join/{list_data['code']}",
    }

def test_add_and_toggle_movie(client, auth_headers):
    # Cria lista primeiro
    code = create_list(client, auth_headers, "Lista de Ação")["code"]

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
    add_res = client.post(f"/lists/{code}/movies", json=movie_payload, headers=auth_headers)
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
    get_movies_res = client.get(f"/lists/{code}/movies", headers=auth_headers)
    assert get_movies_res.status_code == 200
    movies = get_movies_res.json()
    assert len(movies) == 1
    assert movies[0]["watched"] is True

    # Deleta filme
    del_res = client.delete(f"/lists/movies/{movie_id}", headers=auth_headers)
    assert del_res.status_code == 200
    
    # Verifica lista vazia
    movies_after_del = client.get(f"/lists/{code}/movies", headers=auth_headers).json()
    assert len(movies_after_del) == 0


def test_movies_endpoint_supports_pagination(client, auth_headers):
    code = create_list(client, auth_headers, "Lista Paginada")["code"]
    for tmdb_id in (603, 27205, 550):
        response = client.post(
            f"/lists/{code}/movies",
            json={"title": f"Filme {tmdb_id}", "tmdbId": tmdb_id},
            headers=auth_headers,
        )
        assert response.status_code == 200

    first_page = client.get(
        f"/lists/{code}/movies?page=1&page_size=2",
        headers=auth_headers,
    )
    assert first_page.status_code == 200
    assert first_page.json()["total"] == 3
    assert len(first_page.json()["items"]) == 2
    assert first_page.json()["has_next"] is True

    second_page = client.get(
        f"/lists/{code}/movies?page=2&page_size=2",
        headers=auth_headers,
    )
    assert len(second_page.json()["items"]) == 1
    assert second_page.json()["has_next"] is False

def test_add_comment_and_rating(client, auth_headers):
    # Cria lista e adiciona filme
    code = create_list(client, auth_headers, "Cinema Clube")["code"]
    movie_res = client.post(
        f"/lists/{code}/movies",
        json={"title": "Inception", "tmdbId": 27205, "releaseYear": "2010"},
        headers=auth_headers
    )
    movie_id = movie_res.json()["id"]

    # Adiciona comentário com nota
    comment_payload = {
        "text": "Obra de arte do Christopher Nolan!",
        "rating": 5
    }
    comment_res = client.post(f"/lists/movies/{movie_id}/comments", json=comment_payload, headers=auth_headers)
    assert comment_res.status_code == 200
    comment_data = comment_res.json()
    assert comment_data["text"] == "Obra de arte do Christopher Nolan!"
    assert comment_data["rating"] == 5
    assert comment_data["user_id"] == "1"
    assert comment_data["user_name"] == "tester@example.com"

    # Verifica se o filme na lista traz o comentário
    movies_res = client.get(f"/lists/{code}/movies", headers=auth_headers)
    assert movies_res.status_code == 200
    movie = movies_res.json()[0]
    assert len(movie["comments"]) == 1
    assert movie["comments"][0]["rating"] == 5

def test_add_and_get_draw_history(client, auth_headers):
    # Cria lista
    code = create_list(client, auth_headers, "Sessão Pipoca")["code"]

    # Registra sorteio no histórico
    history_payload = {
        "movie_title": "Interestelar",
        "movie_poster": "https://image.tmdb.org/t/p/w500/interstellar.jpg",
        "draw_type": "roulette",
    }
    post_res = client.post(f"/lists/{code}/history", json=history_payload, headers=auth_headers)
    assert post_res.status_code == 200
    history_data = post_res.json()
    assert history_data["movie_title"] == "Interestelar"
    assert history_data["draw_type"] == "roulette"
    assert history_data["drawn_by"] == "1"
    assert "drawn_at" in history_data

    # Consulta histórico
    get_res = client.get(f"/lists/{code}/history", headers=auth_headers)
    assert get_res.status_code == 200
    history_list = get_res.json()
    assert len(history_list) == 1
    assert history_list[0]["movie_title"] == "Interestelar"

def test_get_list_members(client, auth_headers):
    # Cria lista
    code = create_list(client, auth_headers, "Amigos do Cinema")["code"]

    # Consulta membros da lista
    members_res = client.get(f"/lists/{code}/members", headers=auth_headers)
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
    code = create_list(client, auth_headers, "Clube VIP")["code"]

    # Usuário 2 entra na lista
    join_res = client.post(f"/lists/join/{code}", headers=headers2)
    assert join_res.status_code == 200

    # Verifica se há 2 membros
    members_res = client.get(f"/lists/{code}/members", headers=auth_headers)
    assert len(members_res.json()) == 2
    member2_id = next(m["id"] for m in members_res.json() if m["email"] == "member2@example.com")

    # Usuário 1 (dono) remove usuário 2
    del_res = client.delete(f"/lists/{code}/members/{member2_id}", headers=auth_headers)
    assert del_res.status_code == 200

    # Verifica se agora só restou 1 membro
    members_after = client.get(f"/lists/{code}/members", headers=auth_headers)
    assert len(members_after.json()) == 1

def test_cleanup_old_draw_history(client, auth_headers, db_session):
    from datetime import datetime, timezone, timedelta
    from models.models import DrawHistory, MovieList

    # Cria lista
    code = create_list(client, auth_headers, "Histórico Antigo")["code"]
    db_list = db_session.query(MovieList).filter(MovieList.code == code).first()

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
    get_res = client.get(f"/lists/{code}/history", headers=auth_headers)
    assert len(get_res.json()) == 2

    # Executa arquivamento de registros com mais de 7 dias
    clean_res = client.delete(f"/lists/{code}/history/cleanup?days=7", headers=auth_headers)
    assert clean_res.status_code == 200
    assert clean_res.json()["deleted_count"] == 1

    # Confirma que só restou o registro recente
    get_after = client.get(f"/lists/{code}/history", headers=auth_headers)
    history_after = get_after.json()
    assert len(history_after) == 1
    assert history_after[0]["movie_title"] == "Interestelar Recente"

def test_bola_unauthorized_movie_access_and_modification(client, auth_headers):
    # Usuário 1 (auth_headers) cria uma lista e adiciona um filme
    code = create_list(client, auth_headers, "Lista Privada de A")["code"]
    add_res = client.post(f"/lists/{code}/movies", json={"title": "Matrix", "tmdbId": 603}, headers=auth_headers)
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
    res_get = client.get(f"/lists/{code}/movies", headers=attacker_headers)
    assert res_get.status_code == 403

    # 2. Atacante tenta adicionar filme na lista de A -> 403 Forbidden
    res_add = client.post(f"/lists/{code}/movies", json={"title": "Invasor", "tmdbId": 999}, headers=attacker_headers)
    assert res_add.status_code == 403

    # 3. Atacante tenta marcar o filme de A como assistido -> 403 Forbidden
    res_toggle = client.put(f"/lists/movies/{movie_id}/toggle-watched", headers=attacker_headers)
    assert res_toggle.status_code == 403

    # 4. Atacante tenta deletar o filme de A -> 403 Forbidden
    res_del = client.delete(f"/lists/movies/{movie_id}", headers=attacker_headers)
    assert res_del.status_code == 403

    # 5. Atacante tenta listar membros da lista de A -> 403 Forbidden
    res_members = client.get(f"/lists/{code}/members", headers=attacker_headers)
    assert res_members.status_code == 403

    # 6. Atacante tenta ver o histórico da lista de A -> 403 Forbidden
    res_history = client.get(f"/lists/{code}/history", headers=attacker_headers)
    assert res_history.status_code == 403

def test_websocket_authentication_and_authorization(client, auth_headers):
    # Usuário 1 cria uma lista
    code = create_list(client, auth_headers, "Lista WebSocket")["code"]

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
        with client.websocket_connect(f"/lists/ws/{code}") as ws:
            pass

    # Conexão com token de usuário que não é membro -> deve falhar
    with pytest.raises(Exception):
        with client.websocket_connect(f"/lists/ws/{code}?token={token2}") as ws:
            pass

    # Conexão com token válido do dono -> deve conectar com sucesso
    ticket_res = client.post(f"/lists/{code}/ws-ticket", headers=auth_headers)
    assert ticket_res.status_code == 200
    ticket = ticket_res.json()["ticket"]
    with client.websocket_connect(f"/lists/ws/{code}?ticket={ticket}") as ws:
        assert ws is not None

    # JWT não é aceito como mecanismo de autenticação do WebSocket.
    with pytest.raises(Exception):
        with client.websocket_connect(f"/lists/ws/{code}?token=invalid"):
            pass

def test_delete_list_with_all_relationships(client, auth_headers):
    # 1. Cria lista
    code = create_list(client, auth_headers, "Lista Completa Para Deletar")["code"]

    # 2. Adiciona participante/membro
    client.post("/auth/signup", json={"email": "member_del@example.com", "password": "password123"})
    login_member = client.post(
        "/auth/login",
        data={"username": "member_del@example.com", "password": "password123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    member_token = login_member.json()["access_token"]
    member_headers = {"Authorization": f"Bearer {member_token}"}
    client.post(f"/lists/join/{code}", headers=member_headers)

    # 3. Adiciona filme
    res_movie = client.post(
        f"/lists/{code}/movies",
        json={"title": "O Poderoso Chefão", "tmdbId": 238, "releaseYear": "1972"},
        headers=auth_headers
    )
    assert res_movie.status_code == 200
    movie_id = res_movie.json()["id"]

    # 4. Adiciona comentário no filme
    res_comm = client.post(
        f"/lists/movies/{movie_id}/comments",
        json={"text": "Obra de arte absoluta!", "rating": 5},
        headers=auth_headers
    )
    assert res_comm.status_code == 200

    # 5. Registra sorteio no histórico
    res_hist = client.post(
        f"/lists/{code}/history",
        json={
            "movie_id": movie_id,
            "movie_title": "O Poderoso Chefão",
            "draw_type": "roulette"
        },
        headers=auth_headers
    )
    assert res_hist.status_code == 200

    # 6. Deleta a lista inteira (dono) -> deve deletar sem erro 500
    del_list_res = client.delete(f"/lists/{code}", headers=auth_headers)
    assert del_list_res.status_code == 200
    assert del_list_res.json()["message"] == "Lista removida com sucesso"

    # 7. Verifica que a lista não existe mais
    check_res = client.get(f"/lists/{code}/movies", headers=auth_headers)
    assert check_res.status_code == 404


