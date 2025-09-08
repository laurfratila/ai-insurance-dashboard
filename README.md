# AI-Insurance Dashboard

Hackathon project: **AI-Powered Dashboards Driving Insurance Automation**  
Tech stack: **FastAPI** (backend), **React + Vite** (frontend), **Postgres** (database), **Docker Compose** (DevOps).

---

##  Project Overview
This project delivers **AI-powered dashboards** for insurance operations, enabling real-time monitoring and automation.  

- **Mission Goal:** Provide insurers with dashboards for claims, policies, loss ratios, and operational KPIs.  
- **Data Source:** Synthetic Romanian insurance dataset generated with `synthetic_insurance_ro.py`.  
- **Database Design:**  
  - `raw` → direct CSV imports  
  - `core` → cleaned & typed tables  
  - `marts` → materialized views powering dashboards  
- **Frontend:** React + Vite with Tailwind, shadcn/ui, Framer Motion, Recharts.  
- **Backend:** FastAPI with REST APIs serving marts data.  

---

##  Project Structure
```
.
├─ backend/              # FastAPI app
│   ├─ app/
│   │   ├─ main.py       # backend entrypoint
│   │   └─ routers
│ │ ├─ marts.py # marts endpoints
│ │ └─ overview.py # overview endpoints
│   ├─ scripts/          # data loading + SQL builds
│   │   ├─ load_to_db.py
│   │   ├─ build_core.sql
│   │   ├─ build_marts.sql
│   │   └─ rebuild_analytics.py
│   └─ requirements.txt
├─ frontend/             # React + Vite app
│   ├─ src/
│   │   └─ App.tsx       # dashboard shell (sidebar, charts, KPIs)
│   ├─ package.json
│   └─ Dockerfile
├─ utilities/            # synthetic data generator
│   └─ synthetic_insurance_ro.py
├─ data/                 # generated CSVs
│   └─ out/
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

### 2. Create a virtual environment (optional but recommended)
```bash
# macOS/Linux
python3 -m venv .venv
source .venv/bin/activate

# Windows PowerShell
python -m venv .venv
.venv\\Scripts\\activate
```
Install Python dependencies if needed:
```bash
pip install -r backend/requirements.txt
```

### 3. Create your `.env`
Copy the template and fill in secrets:
```bash
cp .env.example .env
```

Example `.env`:
```env
POSTGRES_USER=appuser
POSTGRES_PASSWORD=apppass
POSTGRES_DB=insurancedb
POSTGRES_PORT=5432

BACKEND_PORT=8000
DATABASE_URL=postgresql+psycopg2://appuser:apppass@db:5432/insurancedb

FRONTEND_PORT=5173
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxx
```

 **Never commit `.env`** — only commit `.env.example`.

### 4. Start the stack with Docker
```bash
docker compose up --build
```
- **Frontend:** http://localhost:5173  
- **Backend:** http://localhost:8000/health  
- **Docs:** http://localhost:8000/docs  

Stop stack:
```bash
docker compose down
```

Reset stack (clean volumes & containers):
```bash
docker compose down --volumes --remove-orphans
```

---

##  Database Setup Tutorial

### Step 1 — Generate synthetic data
```bash
mkdir -p data/out
python utilities/synthetic_insurance_ro.py --policies 12000 --seed 42 --out ./data/out
```

### Step 2 — Create schemas (one-time)
```bash
docker compose exec db psql -U appuser -d insurancedb -c "CREATE SCHEMA IF NOT EXISTS raw;"
docker compose exec db psql -U appuser -d insurancedb -c "CREATE SCHEMA IF NOT EXISTS core;"
docker compose exec db psql -U appuser -d insurancedb -c "CREATE SCHEMA IF NOT EXISTS marts;"
```

### Step 3 — Load CSVs into `raw`
```bash
docker compose exec backend python scripts/load_to_db.py --path /data/out --schema raw --replace
```
Check:
```bash
docker compose exec db psql -U appuser -d insurancedb -c "\dt raw.*"
```

### Step 4 — Build `core` tables
```powershell
Get-Content backend\scripts\build_core.sql | docker compose exec -T db psql -U appuser -d insurancedb -v ON_ERROR_STOP=1
```

### Step 5 — Build marts (aggregations)
```powershell
Get-Content backend\scripts\build_marts.sql | docker compose exec -T db psql -U appuser -d insurancedb -v ON_ERROR_STOP=1
```

### Step 6 — Refresh marts
```bash
docker compose exec backend python scripts/rebuild_analytics.py
```

---

##  API Endpoints

### Default
- **Health check** → `/health`

### Marts
- **Claims by month** → `/api/marts/claims_by_month`
- **Claims by county** → `/api/marts/claims_by_county`

### Overview
- **Loss ratio by month** → `/api/overview/loss_ratio_by_month`
- **Gross written premium (GWP) by period** → `/api/overview/gwp_by_period`
- **Claims frequency by period** → `/api/overview/claims_frequency_by_period`
- **Average settlement time by period** → `/api/overview/avg_settlement_time_by_period`


Example:
```bash
curl http://localhost:8000/api/marts/claims_by_month | jq .
```

---

##  Frontend (React + Vite)
- Built with **Tailwind**, **shadcn/ui**, **lucide-react**, **Framer Motion**, **Recharts**.
- Features:
  - Sidebar navigation
  - Dark mode toggle
  - KPI cards (Policies, Claims, Loss Ratio)
  - Charts (Claims vs Premium)
- Data fetching with **React Query**.

---

##  Team Contributions
- **DevOps (Member 6):** Docker + Compose setup, .env safety, database pipeline.  
- **Backend Team:** FastAPI routers, marts APIs, DB migrations.  
- **Frontend Team:** Dashboard shell, charts, auth pages.  
- **Data/ML:** Synthetic data generation, AI endpoints.  

---

##  Troubleshooting

**CSV files not found**  
- Ensure they exist under `data/out`.  
- Inside container: `docker compose exec backend ls /data/out`  

**Backend can’t see `/data/out`**  
- Check `docker-compose.yml` volumes include `- ./data:/data:ro`.  
- Rebuild: `docker compose up -d --build backend`.  

**`psql: command not found`**  
- Run SQL via the `db` container, not backend.  

**Reset everything**  
```bash
docker compose down --volumes --remove-orphans
docker compose up -d --build
python utilities/synthetic_insurance_ro.py --policies 12000 --seed 42 --out ./data/out
docker compose exec backend python scripts/load_to_db.py --path /data/out --schema raw --replace
docker compose exec backend python scripts/rebuild_analytics.py
```

---

