from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.database import get_db_session
from app.models import Catalogo
from app.dependencies import templates, require_admin, registrar_auditoria

router = APIRouter(prefix="/catalogo-admin", tags=["Catálogo"])

@router.get("", response_class=HTMLResponse)
def catalogo_page(request: Request, sessao: dict = Depends(require_admin), db: Session = Depends(get_db_session)):
    itens = db.query(Catalogo).order_by(Catalogo.linha, Catalogo.modelo).all()
    return templates.TemplateResponse("catalogo.html", {"request": request, "sessao": sessao, "itens": itens})

@router.post("/criar")
def criar_catalogo(request: Request, sessao: dict = Depends(require_admin),
                   linha: str = Form(...), modelo: str = Form(...), db: Session = Depends(get_db_session)):
    existente = db.query(Catalogo).filter(Catalogo.linha == linha.strip(), Catalogo.modelo == modelo.strip()).first()
    if existente:
        raise HTTPException(400, "Modelo já existe nesta linha.")
    
    novo_item = Catalogo(linha=linha.strip(), modelo=modelo.strip())
    db.add(novo_item)
    db.commit()
    registrar_auditoria(sessao.get("usuario", "?"), "catalogo_criado", alvo=f"{linha.strip()} / {modelo.strip()}")
    return RedirectResponse("/catalogo-admin", status_code=303)

@router.post("/{id_c}/toggle")
def toggle_catalogo(id_c: int, request: Request, sessao: dict = Depends(require_admin),
                    ativo: int = Form(...), db: Session = Depends(get_db_session)):
    item = db.query(Catalogo).filter(Catalogo.id == id_c).first()
    if not item:
        raise HTTPException(404, "Item não encontrado")
    
    item.ativo = bool(ativo)
    db.commit()
    acao = "catalogo_ativado" if ativo else "catalogo_desativado"
    registrar_auditoria(sessao.get("usuario", "?"), acao, alvo=f"{item.linha} / {item.modelo}")
    return RedirectResponse("/catalogo-admin", status_code=303)