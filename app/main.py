from fastapi import FastAPI, Request, Response
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.database import engine, Base, SessionLocal
from app.models import Usuario, Soldador, Catalogo
from app.routers import auth, inspecoes, soldadores, usuarios, catalogo as router_catalogo, auditoria

limiter = Limiter(key_func=get_remote_address, default_limits=["100 per minute"])
app = FastAPI(title="Sistema de Qualidade - Soldagem")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

import os

@app.post("/csp-report")
async def csp_report(request: Request):
    # Recebe os relatórios de violação de política de segurança do navegador
    report = await request.json()
    print(f"ALERTA SEGURANÇA: CSP Violation - {report}")
    return {"status": "ok"}


# Garante que a pasta de fotos existe
IMG_DIR = os.getenv("IMG_DIR", "/data/fotos")
os.makedirs(IMG_DIR, exist_ok=True)

# Monta os arquivos estáticos
app.mount("/static", StaticFiles(directory="/app/static"), name="static")
app.mount("/fotos", StaticFiles(directory=IMG_DIR), name="fotos")

# --- LIGA TODAS AS ROTAS DA NOSSA NOVA ARQUITETURA ---
app.include_router(auth.router)
app.include_router(inspecoes.router)
app.include_router(soldadores.router)
app.include_router(usuarios.router)
app.include_router(router_catalogo.router)
app.include_router(auditoria.router)

@app.on_event("startup")
def startup():
    # Isso cria todas as tabelas no PostgreSQL ou SQLite automaticamente!
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    try:
        # Popula soldadores padrão na primeira vez
        if db.query(Soldador).count() == 0:
            for nome in ["Carlos Silva", "João Souza", "Maria Oliveira"]:
                db.add(Soldador(nome=nome))
            db.commit()

        # Popula catálogo padrão na primeira vez
        if db.query(Catalogo).count() == 0:
            catalogo_inicial = {
                "Linha Leite": ["RA-100 - Resfriador Aberto", "MC-200 - Meia Cana", "FH-300 - Fechado Horizontal", "FV-400 - Vertical"],
                "Linha Industrial": ["IS-500 - Isotérmico", "MX-600 - Mistura", "ES-700 - Estocagem", "PR-800 - Processo"],
                "Tinas de Sorvete": ["MT-900 - Maturadora", "MG-910 - Maturadora Gás", "PT-920 - Pasteurizadora"],
            }
            for linha, modelos in catalogo_inicial.items():
                for modelo in modelos:
                    db.add(Catalogo(linha=linha, modelo=modelo))
            db.commit()

        # Garante o usuário lucas (Admin default) via variável de ambiente
        HASH_KEVIN = os.getenv("HASH_KEVIN", "").strip().strip('"\'').strip()
        if HASH_KEVIN.startswith('$2b$') and len(HASH_KEVIN) >= 59:
            admin = db.query(Usuario).filter(Usuario.usuario == 'kevin').first()
            if not admin:
                db.add(Usuario(usuario='kevin', nome='Kevin', hash_senha=HASH_KEVIN, papel='admin'))
            else:
                admin.hash_senha = HASH_KEVIN
                admin.papel = 'admin'
            db.commit()
            
    finally:
        db.close()