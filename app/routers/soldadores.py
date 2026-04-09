# app/routers/soldadores.py
from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse

from app.schemas.soldador import SoldadorCreate
from app.services.soldador import SoldadorService
from app.services.auditoria import registrar_auditoria
from app.dependencies import templates, require_admin, verificar_csrf, provide_soldador_service

router = APIRouter(prefix="/soldadores", tags=["Soldadores"])

@router.get("", response_class=HTMLResponse)
def soldadores_page(request: Request, sessao: dict = Depends(require_admin), service: SoldadorService = Depends(provide_soldador_service)):
    # Delegamos para o service
    soldadores = service.list_all()
    # Para o template, precisamos ordená-los. O repositório já poderia ordenar? 
    # Como BaseRepository.find_all não tem order_by genérico, organizamos em memória:
    soldadores = sorted(soldadores, key=lambda x: x.nome)
    
    return templates.TemplateResponse("soldadores.html", {
        "request": request, "sessao": sessao, "soldadores": soldadores
    })

@router.post("/criar")
def criar_soldador(request: Request, sessao: dict = Depends(require_admin),
                   _csrf: None = Depends(verificar_csrf),
                   nome: str = Form(...), service: SoldadorService = Depends(provide_soldador_service)):
    
    # Validation com Pydantic acontece dentro ou antes. 
    # Validando via schema para testar Pydantic validation:
    try:
        dados = SoldadorCreate(nome=nome).model_dump()
        service.criar_soldador(dados, usuario_logado_id=sessao.get("usuario", "?"))
    except ValueError as e:
        raise HTTPException(400, str(e))
        
    return RedirectResponse("/soldadores", status_code=303)

@router.post("/{id_s}/toggle")
def toggle_soldador(id_s: int, request: Request, sessao: dict = Depends(require_admin),
                    _csrf: None = Depends(verificar_csrf),
                    ativo: int = Form(...), service: SoldadorService = Depends(provide_soldador_service)):
    
    soldador = service.toggle(id_s, "ativo")
    
    # Auditoria manual se o service toggle base não tiver:
    acao = "soldador_ativado" if ativo else "soldador_desativado"
    registrar_auditoria(service.db, sessao.get("usuario", "?"), acao, alvo=soldador.nome)
    service.db.commit() # Unit of work manual para os passos acoplados à auditoria extra da rota
    
    return RedirectResponse("/soldadores", status_code=303)