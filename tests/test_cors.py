def test_cors_allowed_localhost(client):
    headers = {
        "Origin": "http://localhost:5173",
        "Access-Control-Request-Method": "GET"
    }
    response = client.options("/ping", headers=headers)
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"

def test_cors_allowed_production_domain(client):
    headers = {
        "Origin": "https://cine-random.vercel.app",
        "Access-Control-Request-Method": "GET"
    }
    response = client.options("/ping", headers=headers)
    assert response.headers.get("access-control-allow-origin") == "https://cine-random.vercel.app"

def test_cors_allowed_vercel_preview(client):
    headers = {
        "Origin": "https://cine-random-preview-123.vercel.app",
        "Access-Control-Request-Method": "GET"
    }
    response = client.options("/ping", headers=headers)
    assert response.headers.get("access-control-allow-origin") == "https://cine-random-preview-123.vercel.app"

def test_cors_disallowed_untrusted_origin(client):
    headers = {
        "Origin": "https://malicious-site.example.com",
        "Access-Control-Request-Method": "GET"
    }
    response = client.options("/ping", headers=headers)
    assert response.headers.get("access-control-allow-origin") is None
