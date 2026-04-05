# app/dependencies.py
import os
import json
import hashlib
import base64
from datetime import datetime
from fastapi import Request, HTTPException, Depends
from fastapi.templating import Jinja2Templates
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from cryptography.fernet import Fernet

from app.database import SessionLocal
from app.models import Auditoria

_raw_secret = os.getenv("SECRET_KEY", "troque-em-producao-use-valor-longo-aleatorio")
if _raw_secret == "troque-em-producao-use-valor-longo-aleatorio":
    print("AVISO: Usando SECRET_KEY padrão! Altere isso em produção para segurança real.")

SECRET_KEY = _raw_secret
# Derivamos uma chave Fernet a partir da SECRET_KEY para criptografar os dados da sessão
_fernet_key = base64.urlsafe_b64encode(hashlib.sha256(SECRET_KEY.encode()).digest())
_fernet = Fernet(_fernet_key)

TIMEOUT_MIN = int(os.getenv("SESSION_TIMEOUT_MINUTES", 60))
serializer = URLSafeTimedSerializer(SECRET_KEY)

# Centralizamos os templates aqui para serem usados em qualquer router
templates = Jinja2Templates(directory="/app/templates")

def criar_sessao(nome: str, usuario: str, papel: str) -> str:
    payload = json.dumps({
        "nome": nome, "usuario": usuario, "papel": papel,
        "ts": datetime.now().isoformat()
    })
    cifrado = _fernet.encrypt(payload.encode()).decode()
    return serializer.dumps(cifrado)

def ler_sessao(token: str):
    try:
        cifrado = serializer.loads(token, max_age=TIMEOUT_MIN * 60)
        decifrado = _fernet.decrypt(cifrado.encode()).decode()
        return json.loads(decifrado)
    except Exception:
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