# app/database.py
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base

DB_FILE = os.getenv("DB_FILE", "/data/dados_inspecoes.db")

# A grande jogada: se tivermos a variável DATABASE_URL (que usaremos com Postgres), 
# ele usa, senão, faz fallback para o SQLite que você já tem.
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DB_FILE}")

# Argumentos específicos para o SQLite não travar com múltiplas threads
connect_args = {"check_same_thread": False} if SQLALCHEMY_DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Dependência do FastAPI para injetar a sessão do banco de dados nas rotas
def get_db_session():
    db = SessionLocal()
    try:
        # Mantém o modo WAL para SQLite, conforme seu código original
        if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
            db.execute(text("PRAGMA journal_mode=WAL"))
        yield db
    finally:
        db.close()