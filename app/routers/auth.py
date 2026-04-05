import os
from datetime import datetime, timedelta
import bcrypt
from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.database import get_db_session
from app.models import Usuario, TentativaLogin
from app.dependencies import templates, registrar_auditoria, criar_sessao, TIMEOUT_MIN, get_sessao

router = APIRouter(tags=["Autenticação"])
MAX_TENTATIVAS = int(os.getenv("MAX_LOGIN_ATTEMPTS", 5))

def registrar_tentativa(db: Session, usuario: str, sucesso: bool):
    nova_tentativa = TentativaLogin(usuario=usuario, momento=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), sucesso=int(sucesso))
    db.add(nova_tentativa)
    db.commit()

def verificar_login(db: Session, usuario: str, senha: str):
    usuario = usuario.strip().lower()
    limite = (datetime.now() - timedelta(minutes=15)).strftime("%Y-%m-%d %H:%M:%S")
    
    falhas = db.query(TentativaLogin).filter(
        TentativaLogin.usuario == usuario, TentativaLogin.sucesso == 0, TentativaLogin.momento > limite
    ).count()
    
    if falhas >= MAX_TENTATIVAS:
        return None, None, "bloqueado"
    
    user = db.query(Usuario).filter(Usuario.usuario == usuario, Usuario.ativo == True).first()
    if user:
        try:
            if bcrypt.checkpw(senha.encode(), user.hash_senha.encode()):
                registrar_tentativa(db, usuario, True)
                return user.nome, user.papel, "ok"
        except Exception:
            pass
            
    registrar_tentativa(db, usuario, False)
    return None, None, "invalido"

@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request, erro: str = ""):
    return templates.TemplateResponse("login.html", {"request": request, "erro": erro})

@router.post("/login")
def login_post(request: Request, usuario: str = Form(...), senha: str = Form(...), db: Session = Depends(get_db_session)):
    nome, papel, status_login = verificar_login(db, usuario, senha)
    if status_login == "bloqueado":
        registrar_auditoria(usuario, "login_bloqueado")
        return templates.TemplateResponse("login.html", {"request": request, "erro": "Conta bloqueada. Tente novamente em 15 minutos."})
    elif nome and papel:
        registrar_auditoria(usuario, "login_ok", detalhe=f"papel={papel}")
        token = criar_sessao(nome, usuario.strip().lower(), papel)
        resp = RedirectResponse("/", status_code=303)
        resp.set_cookie("sessao", token, httponly=True, secure=True, samesite="lax", max_age=TIMEOUT_MIN * 60)
        return resp
    
    registrar_auditoria(usuario.strip().lower(), "login_falhou")
    return templates.TemplateResponse("login.html", {"request": request, "erro": "Usuário ou senha incorretos."})



@router.get("/logout")
def logout(request: Request):
    sessao = get_sessao(request)
    if sessao:
        registrar_auditoria(sessao.get("usuario", "?"), "logout")
    resp = RedirectResponse("/login", status_code=303)
    resp.delete_cookie("sessao")
    return resp