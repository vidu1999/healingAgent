# SentinelOps AI

Locally AI-powered, security-first autonomous DevOps monitoring and repair platform.

- Backend: Python 3.11+ (target 3.12+) / FastAPI, SQLAlchemy, Alembic
- Frontend: Next.js App Router, React, TypeScript, Tailwind CSS
- Database: PostgreSQL (production) / SQLite (dev fallback, documented)
- AI: Ollama local inference (zero paid AI API budget)
- GitHub: read-only by default; writes require explicit human approval
- Sandbox: Docker-based restricted worker
- Approvals: mandatory explicit human approval before every external mutation

## Status

Implementation in progress on branch `arena/a0347bf3-healingagent`. Infrastructure
(Docker, Ollama, GitHub credentials) is not available in this sandbox; the
application is built with deterministic fakes so the full test suite runs
offline. See docs/ and PHASE notes below.

## Repository layout

```
backend/          FastAPI application, SQLAlchemy models, Alembic migrations, tests
apps/web/         Next.js App Router frontend
worker/           Docker-based restricted verification worker
infra/            Docker Compose, PostgreSQL, monitoring
scripts/          PowerShell setup/dev/test/lint scripts (Windows 11)
docs/             Architecture, setup, security, operations, backup-restore
```

## Quick start (development, Windows PowerShell)

Prerequisites: Git, Python 3.12+, Node.js LTS, Docker Desktop (Linux containers),
Ollama for Windows, a downloaded coding model.

```powershell
# 1. Backend
cd backend
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[dev]"
# copy and edit .env (backend/.env)
copy ..\.env.example .env
# 2. Database (PostgreSQL via Docker, or sqlite dev fallback)
# 3. Migrations
alembic upgrade head
# 4. Start backend
uvicorn app.main:app --reload --port 8000
# 5. Frontend (new terminal)
cd ../apps/web
npm ci
npm run dev
# 6. Worker (requires Docker)
# cd ../worker && docker build -t sentinelops-worker:latest .
```

## Testing

```powershell
cd backend
pytest -q
```

Tests that require Docker, Ollama, or GitHub credentials are marked and skipped
without that infrastructure. See docs/testing.md.

## Security

All external mutations require explicit human approval through the central
approval engine. Raw secrets are never stored, logged, or sent to the model.
See docs/security.md and docs/threat-model.md.

## License

Private - internal portfolio project.
