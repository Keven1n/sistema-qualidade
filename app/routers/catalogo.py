from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse

from app.schemas.catalogo import CatalogoCreate
from app.services.catalogo import CatalogoService
from app.services.auditoria import registrar_auditoria
from app.dependencies import templates, require_admin, verificar_csrf, provide_catalogo_service

router = APIRouter(prefix="/catalogo-admin", tags=["Catálogo"])

@router.get("", response_class=HTMLResponse)
def catalogo_page(request: Request, sessao: dict = Depends(require_admin), service: CatalogoService = Depends(provide_catalogo_service)):
    itens = service.list_all()
    # Emulando orderBy antigo em memoria
    itens = sorted(itens, key=lambda x: (x.linha, x.modelo))
    return templates.TemplateResponse("catalogo.html", {"request": request, "sessao": sessao, "itens": itens})

@router.post("/criar")
def criar_catalogo(request: Request, sessao: dict = Depends(require_admin),
                   _csrf: None = Depends(verificar_csrf),
                   linha: str = Form(...), modelo: str = Form(...), service: CatalogoService = Depends(provide_catalogo_service)):
    try:
        dados = CatalogoCreate(linha=linha, modelo=modelo).model_dump()
        
        existente = service.repo.db.query(service.repo.model).filter(
            service.repo.model.linha == dados['linha'], 
            service.repo.model.modelo == dados['modelo']
        ).first()
        
        if existente:
            raise ValueError("Modelo já existe nesta linha.")
            
        criado = service.repo.create(service.repo.model(**dados))
        registrar_auditoria(service.repo.db, sessao.get("usuario", "?"), "catalogo_criado", alvo=f"{dados['linha']} / {dados['modelo']}")
        service.repo.db.commit()
    except ValueError as e:
        raise HTTPException(400, str(e))

    return RedirectResponse("/catalogo-admin", status_code=303)

@router.post("/{id_c}/toggle")
def toggle_catalogo(id_c: int, request: Request, sessao: dict = Depends(require_admin),
                    _csrf: None = Depends(verificar_csrf),
                    ativo: int = Form(...), service: CatalogoService = Depends(provide_catalogo_service)):
    
    item = service.toggle(id_c, "ativo")
    
    acao = "catalogo_ativado" if ativo else "catalogo_desativado"
    registrar_auditoria(service.db, sessao.get("usuario", "?"), acao, alvo=f"{item.linha} / {item.modelo}")
    service.db.commit()
    
    return RedirectResponse("/catalogo-admin", status_code=303)