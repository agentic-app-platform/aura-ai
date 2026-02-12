## Aura AI

AI-powered shopping assistant API built with **FastAPI** and **LangGraph**. It orchestrates multiple specialized agents (research, styling, ranking, clarification) to help users discover and refine product choices, backed by a relational database, vector embeddings, and optional S3 image handling.

### Features

- **Multi-agent workflow**: Context, research, styling, ranking, and clarification agents wired together via `langgraph`.
- **Chat sessions**: Persistent chat rooms and agent state per user.
- **User profiles**: Body sizes, region, gender, age group, preferences, liked items, and photos.
- **Product embeddings**: Similarity search and ranking for products.
- **Image + S3 support**: Presigned upload URLs and merged / styled image flows.
- **REST API**: FastAPI-based, CORS-enabled, ready to be consumed from a web frontend.

### Tech Stack

- **Backend**: Python 3.12, FastAPI
- **Orchestration**: LangGraph, LangChain
- **Models / LLMs**: OpenAI / Google (via `google-genai`, `langchain-openai`, and related libs)
- **Database**: SQLite for local dev, PostgreSQL for production (via `sqlmodel`, `asyncpg`, `psycopg2-binary`, `langgraph-checkpoint-postgres`)
- **Storage**: AWS S3 (via `boto3`)
- **Other**: Supabase client, SerpAPI, NumPy, Pillow, WebSockets

### Setup

- **Prerequisites**
  - Python **3.12+**
  - Access keys/tokens for the services you actually intend to use (OpenAI, Google, AWS, SerpAPI, DB, etc.).

- **Install dependencies**

  Using `uv` (recommended if you already have it):

  ```bash
  cd /Users/sauravjha/Desktop/aura-ai
  uv sync
  ```

  Or with `pip`:

  ```bash
  cd /Users/sauravjha/Desktop/aura-ai
  python -m venv .venv
  source .venv/bin/activate  # on Windows: .venv\Scripts\activate
  pip install -e .
  ```

- **Environment variables**

  The app reads configuration from `.env` via `app/config.py`. At minimum you should define:

  ```env
  # Database
  DATABASE_URL=sqlite:///database.db            # dev default
  # or e.g. postgres+asyncpg://user:pass@host:5432/dbname

  # LLM / external APIs (set the ones you actually use)
  OPENAI_API_KEY=...
  GOOGLE_VERTEX_AI_PROJECT_ID=...
  SERPAPI_API_KEY=...

  # AWS S3 (if using image upload / storage)
  AWS_ACCESS_KEY_ID=...
  AWS_SECRET_ACCESS_KEY=...
  AWS_REGION=us-east-1
  AWS_S3_BUCKET=your-bucket-name
  S3_PRESIGNED_URL_EXPIRY=3600
  ```

### Running the API

From the project root:

```bash
uvicorn main:app --reload
```

By default, FastAPI will start on `http://127.0.0.1:8000`.

- **Health checks**
  - `GET /` – basic status + whether the LangGraph is initialized
  - `GET /health` – simple health endpoint

On startup, the app:

- Creates/validates database tables via `create_db_and_tables`.
- Initializes an in-memory LangGraph checkpointer.
- Compiles the multi-agent graph via `app.graph.create_graph`.
- Initializes `UserService`.

### Core API Endpoints (overview)

This is not exhaustive, but the key flows exposed by `main.py` include:

- **User**
  - `POST /api/login` – create or fetch a user by username; returns a profile.
  - `GET /api/user/{username}` – fetch user + profile.
  - `PUT /api/update/{username}` – update profile (supports JSON and form-data).

- **Images / S3**
  - Endpoints around generating upload URLs and handling user image uploads (see `s3_service` and related routes in `main.py`).

- **Chat / Agent state**
  - `POST /api/chats` – create a new chat for a user (via `CreateChatRequest`).
  - `GET /api/chats/{user_id}` – list chats (`ChatInfo` with reconstructed messages from agent state).
  - Streaming / non-streaming chat endpoints for sending user messages and receiving assistant responses, flowing through the LangGraph agents (`context`, `research`, `styling`, `ranking`, `clarification`).

For concrete request/response shapes, refer to:

- `api_models/chat.py` – `ChatRequest`, `ChatResponse`
- `api_models/user.py` – login, update, like, and chat metadata models

### Development Notes

- **Database migrations / verification**
  - `migrate_schema.py`, `migrate_agent_state_schema.py` – helpers for evolving DB schema.
  - `verify_db.py`, `verify_graph.py` – basic sanity checks.

- **Agents and tools**
  - Agents: `app/agents/` – `context.py`, `research.py`, `styling.py`, `ranking.py`, `clarification.py`.
  - Tools: `app/tools/` – embeddings, Google Shopping, extraction, filtering, image merging, etc.
  - Graph wiring: `app/graph.py` – defines the state machine and routing.

### Running Tests

There is no formal test harness wired up in this repo yet. If you care about not breaking things every time you touch the agents or schema, add at least:

- Unit tests for agents (pure business logic without external I/O).
- Integration tests hitting key FastAPI routes via `httpx.AsyncClient` or `fastapi.testclient`.

### License

This project is licensed under the **Apache 2.0** license. See `LICENSE` for details.


