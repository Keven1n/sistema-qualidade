from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
import bcrypt

from app.database import get_db_session
from app.models import Usuario
from app.dependencies import templates, require_admin, registrar_auditoria, verificar_csrf

router = APIRouter(prefix="/usuarios", tags=["Usuários"])
PAPEIS_VALIDOS = {"admin", "inspetor", "visitante"}

@router.get("", response_class=HTMLResponse)
def usuarios_page(request: Request, sessao: dict = Depends(require_admin), db: Session = Depends(get_db_session)):
    users = db.query(Usuario).all()
    return templates.TemplateResponse("usuarios.html", {
        "request": request, "sessao": sessao,
        "users": users, "papeis": sorted(PAPEIS_VALIDOS)
    })

@router.post("/criar")
def criar_usuario(request: Request, sessao: dict = Depends(require_admin),
                  _csrf: None = Depends(verificar_csrf),
                  novo_usuario: str = Form(...), novo_nome: str = Form(...),
                  nova_senha: str = Form(...), novo_papel: str = Form(default="inspetor"),
                  db: Session = Depends(get_db_session)):
    if len(nova_senha) < 6 or len(nova_senha) > 100:
        raise HTTPException(400, "A senha deve ter entre 6 e 100 caracteres.")
    if len(novo_usuario.strip()) > 50 or len(novo_nome.strip()) > 100:
        raise HTTPException(400, "Usuário ou nome excedeu o limite máximo de caracteres.")
    if novo_papel not in PAPEIS_VALIDOS:
        raise HTTPException(400, "Papel inválido.")
    
    existente = db.query(Usuario).filter(Usuario.usuario == novo_usuario.strip().lower()).first()
    if existente:
        raise HTTPException(400, "Usuário já existe.")
    
    h = bcrypt.hashpw(nova_senha.encode(), bcrypt.gensalt()).decode()
    novo_user = Usuario(usuario=novo_usuario.strip().lower(), nome=novo_nome.strip(), hash_senha=h, papel=novo_papel)
    db.add(novo_user)
    db.commit()
    
    registrar_auditoria(sessao.get("usuario", "?"), "usuario_criado", alvo=novo_usuario.strip().lower(), detalhe=f"papel={novo_papel}")
    return RedirectResponse("/usuarios", status_code=303)

@router.post("/{id_user}/toggle")
def toggle_usuario(id_user: int, request: Request, sessao: dict = Depends(require_admin),
                   _csrf: None = Depends(verificar_csrf),
                   ativo: int = Form(...), db: Session = Depends(get_db_session)):
    user = db.query(Usuario).filter(Usuario.id == id_user).first()
    if not user:
        raise HTTPException(404, "Usuário não encontrado")
    
    user.ativo = bool(ativo)
    db.commit()
    acao = "usuario_ativado" if ativo else "usuario_desativado"
    registrar_auditoria(sessao.get("usuario", "?"), acao, alvo=user.usuario)
    return RedirectResponse("/usuarios", status_code=303)

@router.post("/{id_user}/papel")
def alterar_papel(id_user: int, request: Request, sessao: dict = Depends(require_admin),
                  _csrf: None = Depends(verificar_csrf),
                  novo_papel: str = Form(...), db: Session = Depends(get_db_session)):
    if novo_papel not in PAPEIS_VALIDOS:
        raise HTTPException(400, "Papel inválido.")
    user = db.query(Usuario).filter(Usuario.id == id_user).first()
    if not user:
        raise HTTPException(404, "Usuário não encontrado")
    
    papel_antigo = user.papel
    user.papel = novo_papel
    db.commit()
    
    registrar_auditoria(sessao.get("usuario", "?"), "papel_alterado", alvo=user.usuario, detalhe=f"antes={papel_antigo} agora={novo_papel}")
    return RedirectResponse("/usuarios", status_code=303)