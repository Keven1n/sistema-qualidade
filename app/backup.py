#!/usr/bin/env python3
import os
import subprocess
import urllib.parse
import shutil
from datetime import datetime
from pathlib import Path

# Lemos as variáveis de ambiente ou usamos os padrões do docker-compose
BACKUP_DIR  = os.getenv("BACKUP_DIR",  "/data/backups")
BACKUP_KEEP = int(os.getenv("BACKUP_KEEP", 7))
LOG_FILE    = os.path.join(BACKUP_DIR, "backup.log")

# O cron costuma ter um ambiente limpo (sem variáveis de ambiente do Docker),
# por isso fornecemos o valor por defeito igual ao que está no docker-compose.yml
DB_URL = os.getenv("DATABASE_URL", "postgresql://admin:adminpassword@db:5432/qualidade")

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

    if not DB_URL.startswith("postgres"):
        log("ERRO: DATABASE_URL não configurada para Postgres.")
        return False

    # Extrai as credenciais da URL do banco de dados
    parsed = urllib.parse.urlparse(DB_URL)
    user = parsed.username
    password = parsed.password
    host = parsed.hostname
    port = parsed.port or 5432
    db_name = parsed.path.lstrip('/')

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    destino = os.path.join(BACKUP_DIR, f"backup_pg_{ts}.sql")

    # Passa a senha via variável de ambiente para o pg_dump não ficar bloqueado à espera de input
    env = os.environ.copy()
    env["PGPASSWORD"] = password

    # Comando de backup nativo do PostgreSQL
    cmd = ["pg_dump", "-h", host, "-p", str(port), "-U", user, "-d", db_name, "-f", destino]

    try:
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        
        if result.returncode != 0:
            log(f"ERRO ao fazer backup do Postgres: {result.stderr}")
            if Path(destino).exists():
                Path(destino).unlink()
            return False

        tamanho = Path(destino).stat().st_size // 1024
        log(f"OK: backup do Postgres salvo em {destino} ({tamanho} KB)")

        # Remove backups antigos, mantendo apenas os N mais recentes
        arquivos = sorted(Path(BACKUP_DIR).glob("backup_pg_*.sql"))
        excluir  = arquivos[:-BACKUP_KEEP] if len(arquivos) > BACKUP_KEEP else []
        for arq in excluir:
            arq.unlink()
            log(f"  removido backup antigo: {arq.name}")

        # Backup das Fotos e Assinaturas
        fotos_dir = os.getenv("IMG_DIR", "/data/fotos")
        if Path(fotos_dir).exists():
            destino_fotos = os.path.join(BACKUP_DIR, f"backup_fotos_{ts}")
            shutil.make_archive(destino_fotos, 'zip', fotos_dir)
            tamanho_fotos = Path(destino_fotos + '.zip').stat().st_size // 1024
            log(f"OK: backup das fotos salvo em {destino_fotos}.zip ({tamanho_fotos} KB)")
            
            arquivos_fotos = sorted(Path(BACKUP_DIR).glob("backup_fotos_*.zip"))
            excluir_fotos = arquivos_fotos[:-BACKUP_KEEP] if len(arquivos_fotos) > BACKUP_KEEP else []
            for arq in excluir_fotos:
                arq.unlink()
                log(f"  removido backup antigo de fotos: {arq.name}")

        return True

    except Exception as e:
        log(f"ERRO ao executar pg_dump: {e}")
        if Path(destino).exists():
            Path(destino).unlink()
        return False

if __name__ == "__main__":
    import sys
    ok = fazer_backup()
    sys.exit(0 if ok else 1)