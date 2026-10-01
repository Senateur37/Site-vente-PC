# ─── Build stage : dépendances Python ───────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /app

# Dépendances système pour psycopg (PostgreSQL) et Pillow
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt

# ─── Final stage ────────────────────────────────────────────────────────────
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

WORKDIR /app

# Runtime libs uniquement (psycopg binary, Pillow)
RUN apt-get update && apt-get install -y --no-install-recommends \
        libpq5 \
        libjpeg62-turbo \
        libwebp7 \
    && rm -rf /var/lib/apt/lists/*

# Wheels buildées au stage précédent
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir --no-index --find-links=/wheels /wheels/*

# Code source
COPY . .

# Collecte des fichiers statiques au moment du build
# DEBUG=False pour activer WhiteNoise storage, SQLite en mémoire pour éviter DATABASE_URL
RUN SECRET_KEY=build-only-not-used-in-prod \
    DEBUG=False \
    DATABASE_URL=sqlite:////tmp/build.db \
    python manage.py collectstatic --noinput

# Utilisateur non-root
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser \
    && chown -R appuser:appgroup /app
USER appuser

EXPOSE 8000

# Gunicorn : 3 workers pour un petit VPS
CMD ["gunicorn", "techshop.wsgi:application", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "3", \
     "--timeout", "120", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
