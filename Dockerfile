FROM python:3.12-slim

WORKDIR /app

# Adicionamos o postgresql-client para podermos executar o pg_dump nos backups
RUN apt-get update && apt-get install -y --no-install-recommends \
    cron \
    gcc \
    libpq-dev \
    postgresql-client \
    wkhtmltopdf \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/       ./app/
COPY templates/ ./templates/
COPY static/    ./static/

# Cron: backup automático todo o dia às 02:00 e às 14:00
RUN echo "0 2,14 * * * root python3 /app/app/backup.py >> /proc/1/fd/1 2>&1" \
    > /etc/cron.d/backup-qualidade \
    && chmod 0644 /etc/cron.d/backup-qualidade

RUN mkdir -p /data/fotos /data/backups

EXPOSE 8000

# Railway injeta a porta via $PORT; fallback para 8000 em ambiente local
CMD cron && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --app-dir /app