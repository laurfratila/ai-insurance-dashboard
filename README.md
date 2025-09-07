#  AI-Insurance Dashboard

Hackathon project: **AI-Powered Dashboards Driving Insurance Automation**  
Tech stack: **FastAPI** (backend), **React + Vite** (frontend), **Postgres** (database), **Docker Compose** (DevOps).

---

##  Project Structure
```
.
├─ backend/              # FastAPI app
│   ├─ app/
│   │   └─ main.py       # backend entrypoint
│   ├─ Dockerfile
│   └─ requirements.txt
├─ frontend/             # React + Vite app
│   ├─ src/
│   ├─ package.json
│   └─ Dockerfile
├─ docker-compose.yml    # Compose stack (backend, frontend, db)
├─ .env                  # Local secrets (NOT committed)
├─ .env.example          # Template for teammates
└─ .gitignore            # Keeps .env + venv + node_modules safe
```

---

##  Quick Start

### 1. Clone the repo
```bash
git clone <your-repo-url>
cd ai-insurance-dashboard
```

### 2. Create your `.env`
Copy the template and fill in secrets:
```bash
cp .env.example .env
```

#### Example `.env` (don’t commit this file):
```env
# Database
POSTGRES_USER=appuser
POSTGRES_PASSWORD=apppass
POSTGRES_DB=insurancedb
POSTGRES_PORT=5432

# Backend
BACKEND_PORT=8000
DATABASE_URL=postgresql+psycopg2://appuser:apppass@db:5432/insurancedb

# Frontend
FRONTEND_PORT=5173

# OpenAI (for later RAG)
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxx
```

 **Never commit `.env`** — it is ignored by `.gitignore`. Only commit `.env.example`.

---

### 3. Start the stack with Docker
From project root:
```bash
docker compose up --build
```

- **Frontend:** http://localhost:5173  
- **Backend:** http://localhost:8000/health  
- **Docs:** http://localhost:8000/docs  

Stop the stack:
```bash
docker compose down
```

Clean everything (remove volumes & old containers):
```bash
docker compose down --volumes --remove-orphans
```

---

##  Services

###  Backend (FastAPI)
- URL: http://localhost:8000  
- Health check: `/health` → `{"status": "ok"}`  
- Interactive docs: `/docs`  

###  Frontend (React + Vite)
- URL: http://localhost:5173  
- Hot-reload enabled.  
- Will connect to backend APIs.  

###  Database (Postgres)
- Container: `aiins_db`  
- Port: `5432`  
- Username/Password/DB: set in `.env`.  
- For now you can comment it out in `docker-compose.yml` if you just want frontend+backend running.

---

##  Team Notes
- Always copy `.env.example` → `.env` before starting.
- Never commit `.env`.
- If you change ports in `.env`, also adjust `docker-compose.yml`.
- Run with `--remove-orphans` if you see warnings about old containers.

---

