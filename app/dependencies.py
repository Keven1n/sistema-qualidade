# app/dependencies.py
import os
from datetime import datetime
from fastapi import Request, HTTPException, Depends
from fastapi.templating import Jinja2Templates
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

from app.database import SessionLocal
from app.models import Auditoria

SECRET_KEY = os.getenv("SECRET_KEY", "troque-em-producao-use-valor-longo-aleatorio")
TIMEOUT_MIN = int(os.getenv("SESSION_TIMEOUT_MINUTES", 60))
serializer = URLSafeTimedSerializer(SECRET_KEY)

# Centralizamos os templates aqui para serem usados em qualquer router
templates = Jinja2Templates(directory="/app/templates")

def criar_sessao(nome: str, usuario: str, papel: str, demo: bool = False) -> str:
    return serializer.dumps({
        "nome": nome, "usuario": usuario, "papel": papel, 
        "demo": demo, "ts": datetime.now().isoformat()
    })

def ler_sessao(token: str):
    try:
        return serializer.loads(token, max_age=TIMEOUT_MIN * 60)
    except (BadSignature, SignatureExpired):
        return None

def get_sessao(request: Request):
    token = request.cookies.get("sessao")
    return ler_sessao(token) if token else None

def require_auth(request: Request):
    sessao = get_sessao(request)
    if not sessao:
        raise HTTPException(status_code=303, headers={"Location": "/login"})
    return sessao

def require_admin(request: Request):
    sessao = require_auth(request)
    if sessao.get("papel") != "admin":
        raise HTTPException(status_code=403, detail="Acesso restrito a administradores.")
    return sessao

def require_inspetor_ou_admin(request: Request):
    sessao = require_auth(request)
    if sessao.get("papel") not in ("admin", "inspetor"):
        raise HTTPException(status_code=403, detail="Sem permissão para esta ação.")
    return sessao

# Veja como a auditoria fica muito mais limpa com o SQLAlchemy!
def registrar_auditoria(usuario: str, acao: str, alvo: str = None, detalhe: str = None):
    db = SessionLocal()
    try:
        nova_auditoria = Auditoria(usuario=usuario, acao=acao, alvo=alvo, detalhe=detalhe)
        db.add(nova_auditoria)
        db.commit()
    except Exception:
        pass
    finally:
        db.close()