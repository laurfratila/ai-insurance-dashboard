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

# 📦 Team Data Setup: PostgreSQL + Synthetic Data (Step‑by‑step)

> This shows every teammate how to spin up Postgres locally and load the same synthetic dataset we use for the dashboards. No cloud required.

## ✅ Prerequisites
- **Docker Desktop** installed and running
- **Git**
- **Python 3.10+** (only needed if you want to generate CSVs locally)

> Secrets note: copy `.env.example` → `.env` and **never commit** `.env`.

---

## 1) Clone & configure
```bash
# clone and enter repo
git clone <your-repo-url>
cd ai-insurance-dashboard

# create local env file
cp .env.example .env
```

## 2) Start the stack
```bash
docker compose up -d --build
```
- Backend: http://localhost:8000/health  → `{ "status": "ok" }`
- Frontend: http://localhost:5173/

---

## 3) Generate (or obtain) the synthetic CSVs
**Option A — Generate locally** (recommended for reproducibility):
```bash
# macOS/Linux (from repo root)
python utilities/synthetic_insurance_ro.py --policies 12000 --seed 42 --out ./data/out
```
```powershell
# Windows PowerShell (from repo root)
python utilities\synthetic_insurance_ro.py --policies 12000 --seed 42 --out .\data\out
```
**Option B — Use shared CSVs:** if someone already generated CSVs, copy them into `data/out/`.

You should see files like:
```
data/out/customers.csv
data/out/policies.csv
data/out/claims.csv
... (etc)
```

> Compose maps the host folder `./data` into the backend container at `/data`, so inside the container CSVs are visible at **`/data/out`**.

---

## 4) Create DB schemas (one‑time)
```bash
docker compose exec db psql -U appuser -d insurancedb -c "CREATE SCHEMA IF NOT EXISTS raw;"
docker compose exec db psql -U appuser -d insurancedb -c "CREATE SCHEMA IF NOT EXISTS core;"
docker compose exec db psql -U appuser -d insurancedb -c "CREATE SCHEMA IF NOT EXISTS marts;"
```

---

## 5) Load CSVs into `raw.*`
```bash
# uses backend/scripts/load_to_db.py (present in repo)
docker compose exec backend python scripts/load_to_db.py --path /data/out --schema raw --replace
```
Verify:
```bash
docker compose exec db psql -U appuser -d insurancedb -c "\\dt raw.*"
docker compose exec db psql -U appuser -d insurancedb -c "SELECT COUNT(*) FROM raw.policies;"
```

---

## 6) Build typed `core.*` tables from `raw.*`
Run the SQL script to create clean, typed tables (dates/numerics).

**macOS/Linux/Git Bash**
```bash
docker compose exec -T db psql -U appuser -d insurancedb -v ON_ERROR_STOP=1 < backend/scripts/build_core.sql
```
**Windows PowerShell**
```powershell
Get-Content backend\scripts\build_core.sql | docker compose exec -T db psql -U appuser -d insurancedb -v ON_ERROR_STOP=1
```
Verify:
```bash
docker compose exec db psql -U appuser -d insurancedb -c "\\dt core.*"
docker compose exec db psql -U appuser -d insurancedb -c "SELECT COUNT(*) FROM core.policies;"
```

---

## 7) Build marts (pre‑aggregated views for fast dashboards)
Create materialized views used by the frontend charts.

**macOS/Linux/Git Bash**
```bash
docker compose exec -T db psql -U appuser -d insurancedb -v ON_ERROR_STOP=1 < backend/scripts/build_marts.sql
```
**Windows PowerShell**
```powershell
Get-Content backend\scripts\build_marts.sql | docker compose exec -T db psql -U appuser -d insurancedb -v ON_ERROR_STOP=1
```
Verify:
```bash
docker compose exec db psql -U appuser -d insurancedb -c "\\dm marts.*"
docker compose exec db psql -U appuser -d insurancedb -c "SELECT * FROM marts.claims_by_month LIMIT 5;"
```

---

## 8) (Optional) One‑command rebuild after new CSVs
When CSVs change, run:
```bash
# rebuild core + marts
docker compose exec backend python scripts/rebuild_analytics.py
# or only refresh marts
# docker compose exec backend python scripts/refresh_marts.py
```

---

## 9) Use the API from the frontend
The backend exposes read‑only endpoints that serve the marts:
```
GET /api/marts/claims_by_month
GET /api/marts/loss_ratio_by_month
GET /api/marts/claims_by_county
```
Try them in the browser or via curl:
```bash
curl http://localhost:8000/api/marts/claims_by_month | jq .
```

---

## 🧪 Troubleshooting
**CSV files not found**
- Ensure they exist under `data/out` on the host.
- Inside container, list: `docker compose exec backend sh -lc "ls -l /data/out"`.

**Backend can’t see `/data/out`**
- Check `docker-compose.yml` → `backend.volumes` includes `- ./data:/data:ro`.
- Recreate container: `docker compose up -d --build backend`.

**`psql: command not found`**
- Run SQL via the **db** container (steps 6–7), not the backend.

**Role or DB doesn’t exist**
- If you reset volumes, recreate user & DB or re‑up compose to re‑initialize.

**Reset everything**
```bash
docker compose down --volumes --remove-orphans
docker compose up -d --build
python utilities/synthetic_insurance_ro.py --policies 12000 --seed 42 --out ./data/out
# load + rebuild
docker compose exec backend python scripts/load_to_db.py --path /data/out --schema raw --replace
docker compose exec backend python scripts/rebuild_analytics.py
```

> Tip: for consistent results across teammates, always run the generator with the same `--seed` value.

