# app/dependencies.py
import os
import json
import hashlib
import hmac
import base64
from datetime import datetime
from fastapi import Request, HTTPException, Depends, Form
from fastapi.templating import Jinja2Templates
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from cryptography.fernet import Fernet
import logging

from app.database import SessionLocal, get_db_session
from app.models import Auditoria
from app.config import settings

logger = logging.getLogger(__name__)

_raw_secret = settings.secret_key
if _raw_secret == "troque-em-producao-use-valor-longo-aleatorio":
    logger.warning("AVISO: Usando SECRET_KEY padrão! Altere isso em produção para segurança real.")

SECRET_KEY = _raw_secret
# Derivamos uma chave Fernet a partir da SECRET_KEY para criptografar os dados da sessão
_fernet_key = base64.urlsafe_b64encode(hashlib.sha256(SECRET_KEY.encode()).digest())
_fernet = Fernet(_fernet_key)

TIMEOUT_MIN = settings.session_timeout_minutes
serializer = URLSafeTimedSerializer(SECRET_KEY)

# Centralizamos os templates aqui para serem usados em qualquer router
templates = Jinja2Templates(directory="/app/templates")

# ── CSRF ────────────────────────────────────────────────────────────────────
def gerar_csrf_token(sessao: dict) -> str:
    """Gera um token CSRF vinculado à sessão do usuário via HMAC-SHA256."""
    msg = f"{sessao.get('usuario','')}:{sessao.get('ts','')}".encode()
    return hmac.new(SECRET_KEY.encode(), msg, hashlib.sha256).hexdigest()

def verificar_csrf(request: Request, csrf_token: str = Form(default="")):
    """Dependency: valida o CSRF token enviado no form contra o da sessão."""
    sessao = get_sessao(request)
    if not sessao:
        raise HTTPException(status_code=403, detail="Sessão inválida.")
    esperado = gerar_csrf_token(sessao)
    if not hmac.compare_digest(csrf_token, esperado):
        raise HTTPException(status_code=403, detail="Token CSRF inválido. Recarregue a página e tente novamente.")

# Registra o helper de CSRF como global Jinja2 (disponível em todos os templates)
templates.env.globals["csrf_token"] = gerar_csrf_token

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

from app.services import get_usuario_service, get_auth_service, get_inspecao_service, get_soldador_service, get_catalogo_service

def provide_usuario_service(db = Depends(get_db_session)): return get_usuario_service(db)
def provide_auth_service(db = Depends(get_db_session)): return get_auth_service(db)
def provide_inspecao_service(db = Depends(get_db_session)): return get_inspecao_service(db)
def provide_soldador_service(db = Depends(get_db_session)): return get_soldador_service(db)
def provide_catalogo_service(db = Depends(get_db_session)): return get_catalogo_service(db)