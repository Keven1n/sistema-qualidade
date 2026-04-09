import os
from datetime import datetime, timedelta
from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse

from app.services.usuario import AuthService
from app.services.auditoria import registrar_auditoria
from app.dependencies import templates, criar_sessao, TIMEOUT_MIN, get_sessao, provide_auth_service

router = APIRouter(tags=["Autenticação"])

@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request, erro: str = ""):
    return templates.TemplateResponse("login.html", {"request": request, "erro": erro})

@router.post("/login")
def login_post(request: Request, usuario: str = Form(...), senha: str = Form(...), 
               auth_service: AuthService = Depends(provide_auth_service)):
               
    # Como deixamos o AuthService como mock temporario na Fase 3,
    # Reimplementamos a lógica de rate limiting robusta localmente usando SQL Alchemy 
    # mantendo os repositórios injetados do DB.
    
    usuario_fmt = usuario.strip().lower()
    MAX_TENTATIVAS = int(os.getenv("MAX_LOGIN_ATTEMPTS", 5))
    limite = (datetime.now() - timedelta(minutes=15)).strftime("%Y-%m-%d %H:%M:%S")
    
    from app.models import TentativaLogin
    from app.models import Usuario
    import bcrypt
    
    falhas = auth_service.db.query(TentativaLogin).filter(
        TentativaLogin.usuario == usuario_fmt, TentativaLogin.sucesso == 0, TentativaLogin.momento > limite
    ).count()
    
    if falhas >= MAX_TENTATIVAS:
        registrar_auditoria(auth_service.db, usuario_fmt, "login_bloqueado")
        auth_service.db.commit()
        return templates.TemplateResponse("login.html", {"request": request, "erro": "Conta bloqueada. Tente novamente em 15 minutos."})
        
    user = auth_service.db.query(Usuario).filter(Usuario.usuario == usuario_fmt, Usuario.ativo == True).first()
    if user:
        try:
            if bcrypt.checkpw(senha.encode(), user.hash_senha.encode()):
                nova_tentativa = TentativaLogin(usuario=usuario_fmt, momento=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), sucesso=1)
                auth_service.db.add(nova_tentativa)
                registrar_auditoria(auth_service.db, usuario_fmt, "login_ok", detalhe=f"papel={user.papel}")
                auth_service.db.commit()
                
                token = criar_sessao(user.nome, usuario_fmt, user.papel)
                resp = RedirectResponse("/", status_code=303)
                resp.set_cookie("sessao", token, httponly=True, secure=True, samesite="lax", max_age=TIMEOUT_MIN * 60)
                return resp
        except Exception:
            pass
            
    nova_tentativa_falha = TentativaLogin(usuario=usuario_fmt, momento=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), sucesso=0)
    auth_service.db.add(nova_tentativa_falha)
    registrar_auditoria(auth_service.db, usuario_fmt, "login_falhou")
    auth_service.db.commit()
    
    return templates.TemplateResponse("login.html", {"request": request, "erro": "Usuário ou senha incorretos."})


@router.get("/logout")
def logout(request: Request, auth_service: AuthService = Depends(provide_auth_service)):
    sessao = get_sessao(request)
    if sessao:
        registrar_auditoria(auth_service.db, sessao.get("usuario", "?"), "logout")
        auth_service.db.commit()
    resp = RedirectResponse("/login", status_code=303)
    resp.delete_cookie("sessao")
    return resp