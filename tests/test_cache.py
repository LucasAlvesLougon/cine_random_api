import time
from utils.cache import InMemoryTTLCache, cache

def test_cache_set_and_get():
    local_cache = InMemoryTTLCache(default_ttl=5)
    local_cache.set("chave_teste", {"filme": "Interestelar"})
    
    val = local_cache.get("chave_teste")
    assert val is not None
    assert val["filme"] == "Interestelar"

def test_cache_ttl_expiration():
    local_cache = InMemoryTTLCache(default_ttl=1)
    local_cache.set("chave_rapida", "dado_temporario", ttl=1)
    
    assert local_cache.get("chave_rapida") == "dado_temporario"
    time.sleep(1.1)
    assert local_cache.get("chave_rapida") is None

def test_cache_delete_and_prefix():
    local_cache = InMemoryTTLCache()
    local_cache.set("movies:listA", [1, 2, 3])
    local_cache.set("movies:listB", [4, 5])
    local_cache.set("users:1", "Lucas")
    
    assert local_cache.size() == 3
    deleted_count = local_cache.delete_prefix("movies:")
    assert deleted_count == 2
    assert local_cache.get("movies:listA") is None
    assert local_cache.get("movies:listB") is None
    assert local_cache.get("users:1") == "Lucas"

def test_api_caching_and_invalidation(client, auth_headers):
    cache.clear()
    
    # 1. Cria lista
    client.post(
        "/lists/",
        json={"name": "Lista Cache", "code": "CACHE01"},
        headers=auth_headers
    )
    
    # 2. Busca filmes (inicialmente vazia, grava em cache)
    res1 = client.get("/lists/CACHE01/movies", headers=auth_headers)
    assert res1.status_code == 200
    assert len(res1.json()) == 0
    assert cache.get("movies:CACHE01") is not None
    
    # 3. Adiciona filme (invalida cache)
    movie_payload = {
        "title": "O Poderoso Chefão",
        "tmdbId": 238,
        "releaseYear": "1972"
    }
    add_res = client.post("/lists/CACHE01/movies", json=movie_payload, headers=auth_headers)
    assert add_res.status_code == 200
    
    # O cache deve ter sido invalidado
    assert cache.get("movies:CACHE01") is None
    
    # 4. Nova busca atualizada
    res2 = client.get("/lists/CACHE01/movies", headers=auth_headers)
    assert res2.status_code == 200
    assert len(res2.json()) == 1
    assert res2.json()[0]["title"] == "O Poderoso Chefão"
    assert cache.get("movies:CACHE01") is not None
