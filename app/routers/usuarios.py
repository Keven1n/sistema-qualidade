from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse

from app.schemas.usuario import UsuarioCreate
from app.services.usuario import UsuarioService
from app.services.auditoria import registrar_auditoria
from app.dependencies import templates, require_admin, verificar_csrf, provide_usuario_service

router = APIRouter(prefix="/usuarios", tags=["Usuários"])
PAPEIS_VALIDOS = {"admin", "inspetor", "visitante"}

@router.get("", response_class=HTMLResponse)
def usuarios_page(request: Request, sessao: dict = Depends(require_admin), service: UsuarioService = Depends(provide_usuario_service)):
    users = service.list_all()
    return templates.TemplateResponse("usuarios.html", {
        "request": request, "sessao": sessao,
        "users": users, "papeis": sorted(PAPEIS_VALIDOS)
    })

@router.post("/criar")
def criar_usuario(request: Request, sessao: dict = Depends(require_admin),
                  _csrf: None = Depends(verificar_csrf),
                  novo_usuario: str = Form(...), novo_nome: str = Form(...),
                  nova_senha: str = Form(...), novo_papel: str = Form(default="inspetor"),
                  service: UsuarioService = Depends(provide_usuario_service)):
    try:
        dados = UsuarioCreate(
            usuario=novo_usuario, 
            nome=novo_nome, 
            senha=nova_senha, 
            papel=novo_papel
        ).model_dump()
        service.criar_novo_usuario(dados, admin_logado_id=sessao.get("usuario", "?"))
    except ValueError as e:
        raise HTTPException(400, str(e))
    
    return RedirectResponse("/usuarios", status_code=303)

@router.post("/{id_user}/toggle")
def toggle_usuario(id_user: int, request: Request, sessao: dict = Depends(require_admin),
                   _csrf: None = Depends(verificar_csrf),
                   ativo: int = Form(...), service: UsuarioService = Depends(provide_usuario_service)):
                   
    user = service.toggle(id_user, "ativo")
    acao = "usuario_ativado" if ativo else "usuario_desativado"
    registrar_auditoria(service.db, sessao.get("usuario", "?"), acao, alvo=user.usuario)
    service.db.commit()
    
    return RedirectResponse("/usuarios", status_code=303)

@router.post("/{id_user}/papel")
def alterar_papel(id_user: int, request: Request, sessao: dict = Depends(require_admin),
                  _csrf: None = Depends(verificar_csrf),
                  novo_papel: str = Form(...), service: UsuarioService = Depends(provide_usuario_service)):
    
    if novo_papel not in PAPEIS_VALIDOS:
        raise HTTPException(400, "Papel inválido.")
        
    service.alterar_papel(id_user, novo_papel, admin_logado_id=sessao.get("usuario", "?"))
    
    return RedirectResponse("/usuarios", status_code=303)