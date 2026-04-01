#!/bin/bash
# Script prático para disparar o backup manual de fora do Container
echo "Iniciando Rotina Oficial de Backup (PostgreSQL + Fotos ZIP)..."
docker compose exec app python3 /app/app/backup.py
echo "✔ Rotina concluída! Acesse os arquivos compactados em ./backups/."
