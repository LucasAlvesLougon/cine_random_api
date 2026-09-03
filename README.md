# Cine Random - API (Backend) ⚙️

Esta é a API que alimenta o **Cine Random**, desenvolvida em **Python 3.11+** com **FastAPI** e **SQLAlchemy 2.0**, seguindo os princípios de **Clean Architecture** (Routers → Services → Repositories).

O backend conta com comunicação bidirecional em tempo real via **WebSockets autenticados**, cache *in-memory* com expiração granular, **Rate Limiting** e blindagem contra vulnerabilidades **BOLA / IDOR**.

---

## 🚀 Tecnologias Principais

* **Python 3.11+** + **FastAPI**: Framework assíncrono de alto desempenho.
* **SQLAlchemy 2.0** + **PostgreSQL** / **SQLite**: Camada de persistência desacoplada com ORM relacional.
* **Pydantic v2**: Validação estrita de contratos de dados e schemas.
* **PyJWT & Bcrypt**: Autenticação com senhas criptografadas e tokens JWT assinados.
* **Google Auth**: Validação nativa de tokens do Google Identity no backend.
* **WebSockets Autenticados**: Broadcast em tempo real por sala (`list_code`) com validação de JWT no handshake.
* **Cache & Rate Limiting In-Memory**: Utilitários thread-safe com algoritmo *Sliding Window* para proteção contra força bruta e DoS.
* **Pytest**: Suíte de testes automatizados cobrindo fluxos felizes, erros e ataques de invasão (**23/23 testes verdes**).

---

## 🛡️ Arquitetura & Segurança

```
routers/       -> Camada de transporte HTTP pura (validação de payload e chamadas ao Service)
services/      -> Lógica de negócio, validação de regras de domínio, BOLA guards e eventos
repositories/  -> Persistência exclusiva e queries no banco de dados via SQLAlchemy
utils/         -> Rate Limiting, Cache com TTL, Notificações e Segurança JWT
```

* **Blindagem BOLA / IDOR:** Qualquer requisição para leitura ou modificação de filmes, membros, comentários ou histórico valida a relação do usuário com a lista (`_verify_list_access`), retornando `403 Forbidden` para invasores.
* **Proteção do WebSocket:** Handshake obrigatório com token JWT (`/lists/ws/{code}?token=...`) e limite de 50 conexões por sala.
* **Rate Limiting:** Rotas `/auth/login` (10 req/min) e `/auth/signup` (5 req/min) protegidas contra força bruta com resposta `429 Too Many Requests` e header `Retry-After`.

---

## 🛠️ Como Executar Localmente

```bash
# 1. Com o gerenciador Astral uv (Recomendado):
uv sync

# 2. Executar o servidor FastAPI em desenvolvimento:
uv run uvicorn main:app --reload --port 8000

# 3. Executar a suíte completa de testes automatizados:
uv run pytest
```

Após iniciar, acesse a documentação interativa OpenAPI / Swagger UI no navegador: `http://localhost:8000/docs`.

