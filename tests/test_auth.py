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

def test_user_can_login_with_verified_google_credential(client, monkeypatch, db_session):
    monkeypatch.setattr(
        "services.auth_service.id_token.verify_oauth2_token",
        lambda token, request, audience: {
            "sub": "google_sub_123456",
            "email": "google.user@example.com",
            "email_verified": True,
            "name": "Google User",
        },
    )

    response = client.post("/auth/google", json={"credential": "valid-google-id-token"})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["email"] == "google.user@example.com"
    assert "user_id" in data

    from models.models import User
    saved_user = db_session.query(User).filter(User.id == data["user_id"]).one()
    assert saved_user.google_sub == "google_sub_123456"


def test_google_login_rejects_forged_token(client, monkeypatch):
    def reject_token(token, request, audience):
        raise ValueError("invalid signature")

    monkeypatch.setattr(
        "services.auth_service.id_token.verify_oauth2_token",
        reject_token,
    )

    response = client.post("/auth/google", json={"credential": "forged.jwt.token"})

    assert response.status_code == 401
    assert response.json()["detail"] == "Credencial do Google inválida ou expirada."


def test_google_login_rejects_unverified_email(client, monkeypatch):
    monkeypatch.setattr(
        "services.auth_service.id_token.verify_oauth2_token",
        lambda token, request, audience: {
            "sub": "google_sub_unverified",
            "email": "unverified@example.com",
            "email_verified": False,
        },
    )

    response = client.post("/auth/google", json={"credential": "valid-but-unverified"})

    assert response.status_code == 401
    assert response.json()["detail"] == "O Google não confirmou este endereço de email."


def test_google_login_rejects_direct_email_without_credential(client):
    response = client.post("/auth/google", json={"email": "victim@example.com"})

    assert response.status_code == 422


def test_google_login_does_not_silently_link_local_account(client, monkeypatch):
    client.post(
        "/auth/signup",
        json={"email": "existing@example.com", "password": "securepassword123"},
    )
    monkeypatch.setattr(
        "services.auth_service.id_token.verify_oauth2_token",
        lambda token, request, audience: {
            "sub": "google_sub_for_existing_email",
            "email": "existing@example.com",
            "email_verified": True,
        },
    )

    response = client.post("/auth/google", json={"credential": "valid-google-id-token"})

    assert response.status_code == 409
    assert "vincular" in response.json()["detail"].lower()


def test_google_login_can_confirm_local_account_with_password(client, monkeypatch, db_session):
    client.post(
        "/auth/signup",
        json={"email": "existing@example.com", "password": "securepassword123"},
    )
    monkeypatch.setattr(
        "services.auth_service.id_token.verify_oauth2_token",
        lambda token, request, audience: {
            "sub": "google_sub_for_existing_email",
            "email": "existing@example.com",
            "email_verified": True,
        },
    )

    response = client.post(
        "/auth/google/confirm-link",
        json={
            "credential": "valid-google-id-token",
            "password": "securepassword123",
        },
    )

    assert response.status_code == 200
    assert response.json()["email"] == "existing@example.com"
    assert "access_token" in response.json()

    from models.models import User

    saved_user = db_session.query(User).filter(User.email == "existing@example.com").one()
    assert saved_user.google_sub == "google_sub_for_existing_email"


def test_google_login_confirmation_rejects_wrong_password_without_linking(
    client, monkeypatch, db_session
):
    client.post(
        "/auth/signup",
        json={"email": "existing@example.com", "password": "securepassword123"},
    )
    monkeypatch.setattr(
        "services.auth_service.id_token.verify_oauth2_token",
        lambda token, request, audience: {
            "sub": "google_sub_for_existing_email",
            "email": "existing@example.com",
            "email_verified": True,
        },
    )

    response = client.post(
        "/auth/google/confirm-link",
        json={
            "credential": "valid-google-id-token",
            "password": "wrongpassword",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Email ou senha incorretos."

    from models.models import User

    saved_user = db_session.query(User).filter(User.email == "existing@example.com").one()
    assert saved_user.google_sub is None


def test_authenticated_user_can_link_matching_google_account(client, auth_headers, monkeypatch, db_session):
    monkeypatch.setattr(
        "services.auth_service.id_token.verify_oauth2_token",
        lambda token, request, audience: {
            "sub": "google_sub_for_existing_email",
            "email": "tester@example.com",
            "email_verified": True,
        },
    )

    response = client.post(
        "/auth/google/link",
        headers=auth_headers,
        json={"credential": "valid-google-id-token"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "detail": "Conta Google vinculada com sucesso.",
        "email": "tester@example.com",
        "user_id": 1,
    }

    from models.models import User

    saved_user = db_session.query(User).filter(User.email == "tester@example.com").one()
    assert saved_user.google_sub == "google_sub_for_existing_email"


def test_google_link_rejects_different_verified_email(client, auth_headers, monkeypatch):
    monkeypatch.setattr(
        "services.auth_service.id_token.verify_oauth2_token",
        lambda token, request, audience: {
            "sub": "google_sub_for_other_email",
            "email": "other@example.com",
            "email_verified": True,
        },
    )

    response = client.post(
        "/auth/google/link",
        headers=auth_headers,
        json={"credential": "valid-google-id-token"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "O email do Google deve ser o mesmo da conta atual."


def test_google_link_rejects_google_account_linked_to_another_user(client, auth_headers, monkeypatch, db_session):
    from models.models import User

    other_user = User(
        email="other@example.com",
        password_hash="$2b$12$2b2b2b2b2b2b2b2b2b2b2u2b2b2b2b2b2b2b2b2b2b2b2b2b2b2",
        google_sub="google_sub_already_linked",
    )
    db_session.add(other_user)
    db_session.commit()

    monkeypatch.setattr(
        "services.auth_service.id_token.verify_oauth2_token",
        lambda token, request, audience: {
            "sub": "google_sub_already_linked",
            "email": "tester@example.com",
            "email_verified": True,
        },
    )

    response = client.post(
        "/auth/google/link",
        headers=auth_headers,
        json={"credential": "valid-google-id-token"},
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Esta conta Google já está vinculada a outro usuário."


def test_google_login_rejects_missing_subject(client, monkeypatch):
    monkeypatch.setattr(
        "services.auth_service.id_token.verify_oauth2_token",
        lambda token, request, audience: {
            "email": "missing-sub@example.com",
            "email_verified": True,
        },
    )

    response = client.post("/auth/google", json={"credential": "missing-sub"})

    assert response.status_code == 401


def test_demo_login_is_disabled_by_default(client, monkeypatch):
    from config import settings
    monkeypatch.setattr(settings, "ALLOW_DEMO_AUTH", False, raising=False)

    response = client.post("/auth/demo", json={"email": "demo@example.com"})

    assert response.status_code == 404


def test_demo_login_is_never_available_in_production(client, monkeypatch):
    from config import settings
    monkeypatch.setattr(settings, "ALLOW_DEMO_AUTH", True, raising=False)
    monkeypatch.setattr(settings, "ENVIRONMENT", "production", raising=False)

    response = client.post("/auth/demo", json={"email": "demo@example.com"})

    assert response.status_code == 404


def test_demo_login_works_only_when_explicitly_enabled(client, monkeypatch):
    from config import settings
    monkeypatch.setattr(settings, "ALLOW_DEMO_AUTH", True, raising=False)
    monkeypatch.setattr(settings, "ENVIRONMENT", "development", raising=False)

    response = client.post("/auth/demo", json={"email": "demo@example.com"})

    assert response.status_code == 200
    assert response.json()["email"] == "demo@example.com"


def test_password_reset_uses_single_use_expiring_token(client, monkeypatch):
    captured = {}

    def fake_delivery(email, token):
        captured["email"] = email
        captured["token"] = token

    monkeypatch.setattr("services.auth_service.send_password_reset_email", fake_delivery)
    signup = client.post("/auth/signup", json={"email": "reset@example.com", "password": "oldpassword123"})
    assert signup.status_code == 201

    request = client.post("/auth/password-reset/request", json={"email": "reset@example.com"})
    assert request.status_code == 202
    assert request.json()["detail"].startswith("Se o email")
    assert captured["email"] == "reset@example.com"

    confirm = client.post(
        "/auth/password-reset/confirm",
        json={"token": captured["token"], "new_password": "newpassword123"},
    )
    assert confirm.status_code == 200

    login = client.post(
        "/auth/login",
        data={"username": "reset@example.com", "password": "newpassword123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert login.status_code == 200

    reused = client.post(
        "/auth/password-reset/confirm",
        json={"token": captured["token"], "new_password": "anotherpassword123"},
    )
    assert reused.status_code == 400


def test_password_reset_does_not_reveal_unknown_email(client):
    response = client.post("/auth/password-reset/request", json={"email": "unknown@example.com"})

    assert response.status_code == 202
    assert response.json()["detail"].startswith("Se o email")


