FROM python:3.12-slim

WORKDIR /app

# Instala cron para o backup automático
RUN apt-get update && apt-get install -y --no-install-recommends cron \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/       ./app/
COPY templates/ ./templates/
COPY static/    ./static/

# Cron: backup todo dia às 02:00 e às 14:00
# backup.py fica em app/ e é montado via volume (igual ao main.py)
RUN echo "0 2,14 * * * root python3 /app/app/backup.py >> /proc/1/fd/1 2>&1" \
    > /etc/cron.d/backup-qualidade \
    && chmod 0644 /etc/cron.d/backup-qualidade

RUN mkdir -p /data/fotos /data/backups

EXPOSE 8000

# Inicia cron em background e depois uvicorn em foreground
CMD cron && uvicorn app.main:app --host 0.0.0.0 --port 8000 --app-dir /app
