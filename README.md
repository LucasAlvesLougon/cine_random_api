# Cine Random - API (Backend) ⚙️

[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue?logo=python)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.141.1-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![SQLAlchemy 2.0](https://img.shields.io/badge/SQLAlchemy-2.0.52-red)](https://www.sqlalchemy.org/)
[![Pydantic v2](https://img.shields.io/badge/Pydantic-v2.13.5-e92063?logo=pydantic)](https://docs.pydantic.dev/)
[![Pytest](https://img.shields.io/badge/Pytest-23%2F23_Passed-green?logo=pytest)](https://docs.pytest.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Render-336791?logo=postgresql)](https://www.postgresql.org/)

API RESTful assíncrona que alimenta o ecossistema **Cine Random**, desenvolvida em **Python 3.11+** com **FastAPI** e **SQLAlchemy 2.0**, seguindo estritamente os princípios de **Clean Architecture** (Routers → Services → Repositories).

O backend conta com comunicação bidirecional em tempo real via **WebSockets autenticados**, cache *in-memory* thread-safe com invalidação granular, **Rate Limiting** com algoritmo *Sliding Window* e blindagem rigorosa contra vulnerabilidades **BOLA / IDOR**.

---

## 🚀 Tecnologias Principais

* **FastAPI:** Framework assíncrono moderno com validação automática via Pydantic v2 e OpenAPI/Swagger.
* **SQLAlchemy 2.0:** Mapeamento objeto-relacional com suporte a PostgreSQL em produção e SQLite isolado em testes.
* **WebSockets Autenticados:** Broadcast em tempo real por sala (`list_code`) com validação de token JWT no handshake.
* **PyJWT & Bcrypt:** Hashing seguro de senhas e geração de Bearer Tokens assinados.
* **Google Auth:** Validação server-side de tokens Google Identity.
* **Astral uv:** Gerenciamento de dependências e ambientes virtuais ultrarrápido.
* **Pytest & TestClient:** Suíte de testes automatizados com banco isolado em memória (**23/23 testes verdes**).

---

## 🛡️ Arquitetura em Camadas (Clean Architecture)

```
cine_random_api/
├── database/            # Conexão, Engine e SessionLocal (PostgreSQL / SQLite)
├── models/              # Modelos relacionais SQLAlchemy (User, MovieList, Movie, Comment, DrawHistory)
├── schemas/             # Schemas Pydantic v2 para validação de entrada e serialização de saída
├── routers/             # Camada de transporte HTTP pura (validação de payload e rotas)
│   ├── auth.py          # Endpoints de cadastro, login e Google OAuth
│   └── movies.py        # Endpoints de listas, filmes, histórico, membros e WebSocket
├── services/            # Camada de negócio e regras de domínio (BOLA guards, WebSocket broadcasts)
│   ├── auth_service.py  # Regras de autenticação, hashing e emissão de JWT
│   └── movie_service.py # Orquestração de listas, validações e expurgo de histórico
├── repositories/        # Camada de persistência dedicada (queries SQLAlchemy exclusivas)
│   ├── user_repository.py
│   └── movie_repository.py
├── utils/               # Utilitários globais
│   ├── cache.py         # Cache in-memory thread-safe com TTL
│   ├── rate_limit.py    # Rate Limiter Sliding Window por IP/Endpoint
│   └── security.py      # Funções de hash bcrypt, decode e dependência get_current_user
├── tests/               # Suíte de testes automatizados com Pytest
└── main.py              # Ponto de entrada FastAPI, CORS middleware e registro de routers
```

---

## 📋 Tabela de Endpoints da API

### 🔐 Autenticação (`/auth`)
| Método | Rota | Auth | Rate Limit | Descrição |
| :--- | :--- | :---: | :---: | :--- |
| `POST` | `/auth/signup` | ❌ | 5 req/min | Criação de novo usuário com senha criptografada. |
| `POST` | `/auth/login` | ❌ | 10 req/min | Login com email/senha e emissão do token JWT. |
| `POST` | `/auth/google` | ❌ | 10 req/min | Autenticação com Google ID Token. |

### 🎬 Listas e Filmes (`/lists`)
| Método | Rota | Auth | Descrição |
| :--- | :--- | :---: | :--- |
| `GET` | `/lists/my` | `Bearer` | Retorna todas as listas que o usuário possui ou participa. |
| `POST` | `/lists/` | `Bearer` | Cria uma nova lista vinculada ao usuário logado. |
| `POST` | `/lists/join/{code}` | `Bearer` | Entra em uma lista existente através do código. |
| `PUT` | `/lists/{code}` | `Bearer` | Atualiza o nome da lista (apenas proprietário). |
| `DELETE` | `/lists/{code}` | `Bearer` | Remove a lista e todos os filmes associados (apenas proprietário). |
| `GET` | `/lists/{code}/members` | `Bearer` | Retorna todos os membros participantes (protegido por BOLA). |
| `DELETE` | `/lists/{code}/members/{user_id}` | `Bearer` | Remove participante (apenas dono ou o próprio usuário). |
| `GET` | `/lists/{code}/movies` | `Bearer` | Retorna todos os filmes da lista (protegido por BOLA). |
| `POST` | `/lists/{code}/movies` | `Bearer` | Adiciona um filme à lista evitando duplicatas. |
| `PUT` | `/lists/movies/{id}/toggle-watched`| `Bearer` | Alterna o status de assistido do filme. |
| `DELETE` | `/lists/movies/{id}` | `Bearer` | Remove um filme da lista (protegido por BOLA). |
| `POST` | `/lists/movies/{id}/comments` | `Bearer` | Adiciona comentário/resenha ao filme. |
| `GET` | `/lists/{code}/history` | `Bearer` | Consulta o histórico de sorteios da lista. |
| `POST` | `/lists/{code}/history` | `Bearer` | Registra novo sorteio (Roleta ou Match) no histórico. |
| `DELETE` | `/lists/{code}/history/cleanup` | `Bearer` | Exclui sorteios antigos com mais de X dias (padrão: 7 dias). |
| `WS` | `/lists/ws/{code}?token={jwt}` | `JWT` | Conexão WebSocket para sincronização em tempo real. |

---

## ⚙️ Variáveis de Ambiente

Crie um arquivo `.env` na raiz do backend:

```env
# Chave secreta para assinatura dos tokens JWT (obrigatória em produção)
SECRET_KEY=sua_chave_secreta_super_segura_de_no_minimo_32_caracteres

# Algoritmo de assinatura JWT (Padrão: HS256)
ALGORITHM=HS256

# Tempo de expiração do Token em minutos (Padrão: 10080 = 7 dias)
ACCESS_TOKEN_EXPIRE_MINUTES=10080

# URL de conexão com o banco de dados (SQLite local ou PostgreSQL)
DATABASE_URL=sqlite:///./cine_random.db
# Para PostgreSQL: postgresql+psycopg://usuario:senha@host:5432/nome_banco

# Client ID do Google OAuth 2.0 para validação server-side
GOOGLE_CLIENT_ID=seu_client_id.apps.googleusercontent.com
```

---

## 🛠️ Comandos do Projeto

```bash
# 1. Instalar dependências com uv
uv sync

# 2. Executar o servidor FastAPI em desenvolvimento (porta 8000)
uv run uvicorn main:app --reload --port 8000

# 3. Executar a suíte completa de testes com Pytest
uv run pytest
```

Documentação OpenAPI interativa disponível em `http://localhost:8000/docs` e ReDoc em `http://localhost:8000/redoc`.


