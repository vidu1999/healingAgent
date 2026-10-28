# SentinelOps AI backend container image.
# Build: docker build -t sentinelops-backend:latest -f backend/Dockerfile .
# Run:   docker run --env-file backend/.env -p 8000:8000 sentinelops-backend:latest
#
# Security notes:
# - Runs as a non-root user (sentinelops).
# - Docker isolation is a security boundary, not a perfect sandbox: the worker
#   service (see infra/) runs with SANDBOX_NETWORK_DISABLED=true and resource
#   limits, but container escape is still possible for a determined attacker.
#   Treat every container as potentially compromised and enforce least
#   privilege at the host/orchestrator layer.
FROM python:3.11-slim AS runner

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    APP_ENV=production

WORKDIR /app

# System deps: only what is needed to build/run Python packages.
RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates \
        libpq5 \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies.
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Application code.
COPY app ./app
COPY alembic.ini ./alembic.ini
COPY alembic ./alembic

# Non-root runtime user.
RUN useradd --create-home --shell /usr/sbin/nologin sentinelops \
    && chown -R sentinelops:sentinelops /app
USER sentinelops

EXPOSE 8000

# Alembic migrations are applied by the entrypoint (see docker-compose) so the
# image itself only needs to serve. CMD is the dev-friendly fallback.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
