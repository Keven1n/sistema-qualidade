#!/usr/bin/env python3
"""
backup.py — Backup automático do banco SQLite

Como funciona:
  - Usa a API de backup nativa do SQLite (safe hot-backup, sem travar o app)
  - Mantém os últimos N backups (padrão: 7)
  - Grava um log em /data/backups/backup.log
  - Retorna exit code 0 em sucesso, 1 em falha (para alertas no cron)

Uso manual:
  python3 /app/backup.py

Configuração via variáveis de ambiente (mesmas do .env):
  DB_FILE      = /data/dados_inspecoes.db
  BACKUP_DIR   = /data/backups
  BACKUP_KEEP  = 7
"""

import os
import sqlite3
import shutil
from datetime import datetime
from pathlib import Path

DB_FILE     = os.getenv("DB_FILE",     "/data/dados_inspecoes.db")
BACKUP_DIR  = os.getenv("BACKUP_DIR",  "/data/backups")
BACKUP_KEEP = int(os.getenv("BACKUP_KEEP", 7))

LOG_FILE = os.path.join(BACKUP_DIR, "backup.log")

def log(msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    linha = f"[{ts}] {msg}"
    print(linha)
    try:
        with open(LOG_FILE, "a") as f:
            f.write(linha + "\n")
    except Exception:
        pass

def fazer_backup() -> bool:
    Path(BACKUP_DIR).mkdir(parents=True, exist_ok=True)

    if not Path(DB_FILE).exists():
        log(f"ERRO: banco não encontrado em {DB_FILE}")
        return False

    ts       = datetime.now().strftime("%Y%m%d_%H%M%S")
    destino  = os.path.join(BACKUP_DIR, f"backup_{ts}.db")

    try:
        # Backup online via API nativa do SQLite — não bloqueia leituras/escritas do app
        src  = sqlite3.connect(DB_FILE)
        dest = sqlite3.connect(destino)
        src.backup(dest)
        dest.close()
        src.close()

        tamanho = Path(destino).stat().st_size // 1024
        log(f"OK: backup salvo em {destino} ({tamanho} KB)")

        # Remove backups antigos, mantendo apenas os N mais recentes
        arquivos = sorted(Path(BACKUP_DIR).glob("backup_*.db"))
        excluir  = arquivos[:-BACKUP_KEEP] if len(arquivos) > BACKUP_KEEP else []
        for arq in excluir:
            arq.unlink()
            log(f"  removido backup antigo: {arq.name}")

        return True

    except Exception as e:
        log(f"ERRO ao fazer backup: {e}")
        # Remove arquivo incompleto se existir
        if Path(destino).exists():
            Path(destino).unlink()
        return False

if __name__ == "__main__":
    import sys
    ok = fazer_backup()
    sys.exit(0 if ok else 1)
