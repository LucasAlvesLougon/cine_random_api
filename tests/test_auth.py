def test_signup_success(client):
    response = client.post("/auth/signup", json={
        "email": "novo.usuario@example.com",
        "password": "minhasenhaf带有123"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "novo.usuario@example.com"
    assert "id" in data

def test_signup_duplicate_email(client):
    payload = {"email": "duplicado@example.com", "password": "senha123456"}
    first = client.post("/auth/signup", json=payload)
    assert first.status_code == 201
    
    second = client.post("/auth/signup", json=payload)
    assert second.status_code == 400
    assert second.json()["detail"] == "Email já cadastrado."

def test_login_success(client):
    user_payload = {"email": "login.user@example.com", "password": "password123"}
    client.post("/auth/signup", json=user_payload)
    
    response = client.post(
        "/auth/login",
        data={"username": user_payload["email"], "password": user_payload["password"]},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_wrong_password(client):
    user_payload = {"email": "errada@example.com", "password": "correctpassword"}
    client.post("/auth/signup", json=user_payload)
    
    response = client.post(
        "/auth/login",
        data={"username": user_payload["email"], "password": "wrongpassword"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Email ou senha incorretos."

def test_login_nonexistent_user(client):
    response = client.post(
        "/auth/login",
        data={"username": "naoexiste@example.com", "password": "anypassword"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == 401

def test_rate_limit_exceeded(client):
    from utils.rate_limit import limiter
    limiter.clear()

    # Faz 10 requisições seguidas para bater no limite
    for _ in range(10):
        client.post(
            "/auth/login",
            data={"username": "test@test.com", "password": "wrongpassword"},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )

    # A 11ª requisição deve ser bloqueada por Rate Limit
    blocked_res = client.post(
        "/auth/login",
        data={"username": "test@test.com", "password": "wrongpassword"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert blocked_res.status_code == 429
    assert "Retry-After" in blocked_res.headers
    assert "Muitas tentativas" in blocked_res.json()["detail"]
    limiter.clear()

def test_user_can_login_with_google(client):
    payload = {
        "email": "google.user@example.com",
        "name": "Google User",
        "google_id": "google_sub_123456"
    }
    response = client.post("/auth/google", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["email"] == "google.user@example.com"
    assert "user_id" in data

def test_user_can_login_with_google_id_token(client):
    import json
    import base64
    payload_data = {
        "email": "jwt.google@example.com",
        "name": "JWT Google User",
        "sub": "google_sub_jwt_987"
    }
    payload_b64 = base64.urlsafe_b64encode(json.dumps(payload_data).encode()).decode().rstrip("=")
    id_token = f"eyJhbGciOiJSUzI1NiJ9.{payload_b64}.mockSignature"

    response = client.post("/auth/google", json={"idToken": id_token})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["email"] == "jwt.google@example.com"
    assert "user_id" in data

def test_google_login_invalid_email(client):
    response = client.post("/auth/google", json={"email": "email_invalido"})
    assert response.status_code == 422
    assert "O token do Google não contém um e-mail válido" in response.json()["detail"]


