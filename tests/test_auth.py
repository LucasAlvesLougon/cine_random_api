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
