# Cine Random - API (Backend) ⚙️

Esta é a API que alimenta o **Cine Random**, desenvolvida em **Python** usando o framework **FastAPI**. Ela substitui a antiga infraestrutura do Firebase Firestore, garantindo um banco de dados relacional flexível e comunicação multi-player em tempo real.

## Tecnologias Principais
- **FastAPI** (Framework web ultrarrápido com documentação automática)
- **SQLAlchemy** (ORM para modelagem e persistência de dados estruturados)
- **Pydantic** (Validação estrita de dados de entrada e saída)
- **WebSockets** (Para disparo de eventos em tempo real)
- **SQLite / PostgreSQL** (Armazenamento das listas, usuários e filmes)
- **Passlib & PyJWT** (Para geração e validação de chaves eletrônicas JWT)

## Funcionalidades
A API gerencia os fluxos completos da aplicação de forma isolada, documentada e modular:
- **Autenticação:** Login JWT clássico e integração completa com a verificação de Tokens do **Google OAuth**.
- **Listas (CRUD):** Criação de listas, edição de nome de listas, exclusão segura e lógica de adesão de membros via convite.
- **Filmes:** Rotas para associar filmes do TMDB às listas sem duplicatas e inversão de status (`watched`).
- **WebSocket Manager:** Um gerenciador de conexões embutido. Assim que qualquer endpoint altera o estado de um filme, ele faz broadcast automático (`broadcast_refresh`) ordenando o frontend de todos os clientes assistindo aquela lista a se recarregarem simultaneamente.

## Como Executar

A API é configurada de forma moderna utilizando `uv` para gestão de dependências.

```bash
# 1. Caso use uv (Altamente recomendado):
uv sync

# 1.1 Caso use Pip/venv padrão:
python -m venv .venv
# ative a venv: .venv\Scripts\activate
# instale dependências do pyproject.toml ou pip install -r requirements.txt se existir

# 2. Execute o servidor uvicorn
uvicorn main:app --reload
```

Após iniciar, basta acessar a documentação automática da sua API visitando `http://localhost:8000/docs` no navegador. Lá você pode testar todos os endpoints!
