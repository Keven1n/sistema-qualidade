FROM python:3.12-slim

WORKDIR /app

# Dependencias de sistema: backup (pg_dump), cron e WeasyPrint (cairo/pango)
RUN apt-get update && apt-get install -y --no-install-recommends \
    cron \
    gcc \
    libpq-dev \
    postgresql-client \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    shared-mime-info \
    fontconfig \
    fonts-liberation \
    gosu \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/       ./app/
COPY templates/ ./templates/
COPY static/    ./static/

# Criar usuário não-root e ajustar permissões
RUN useradd -m -s /bin/bash appuser && \
    mkdir -p /data/fotos /data/backups && \
    chown -R appuser:appuser /app /data

# Cron: backup automático todo o dia às 02:00 e às 14:00 (rodando como appuser)
RUN echo "0 2,14 * * * appuser python3 /app/app/backup.py >> /proc/1/fd/1 2>&1" \
    > /etc/cron.d/backup-qualidade \
    && chmod 0644 /etc/cron.d/backup-qualidade

EXPOSE 8000

# Script de entrypoint inline: garante permissões dos volumes antes de rodar, inicia cron como root e uvicorn como appuser
CMD chown -R appuser:appuser /data && \
    cron && \
    gosu appuser uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --app-dir /app --proxy-headers --forwarded-allow-ips="*"