# app/routers/soldadores.py
from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.database import get_db_session
from app.models import Soldador
from app.dependencies import templates, require_admin, registrar_auditoria

# O prefixo indica que todas as rotas aqui começam por /soldadores
router = APIRouter(prefix="/soldadores", tags=["Soldadores"])

@router.get("", response_class=HTMLResponse)
def soldadores_page(request: Request, sessao: dict = Depends(require_admin), db: Session = Depends(get_db_session)):
    # SQLAlchemy em ação! Substitui as strings SQL puras.
    soldadores = db.query(Soldador).order_by(Soldador.nome).all()
    return templates.TemplateResponse("soldadores.html", {
        "request": request, "sessao": sessao, "soldadores": soldadores
    })

@router.post("/criar")
def criar_soldador(request: Request, sessao: dict = Depends(require_admin), 
                   nome: str = Form(...), db: Session = Depends(get_db_session)):
    
    # Verifica se já existe um soldador com esse nome
    existente = db.query(Soldador).filter(Soldador.nome == nome.strip()).first()
    if existente:
        raise HTTPException(400, "Soldador já existe.")
        
    novo_soldador = Soldador(nome=nome.strip())
    db.add(novo_soldador)
    db.commit()
    
    registrar_auditoria(sessao.get("usuario", "?"), "soldador_criado", alvo=nome.strip())
    return RedirectResponse("/soldadores", status_code=303)

@router.post("/{id_s}/toggle")
def toggle_soldador(id_s: int, request: Request, sessao: dict = Depends(require_admin),
                    ativo: int = Form(...), db: Session = Depends(get_db_session)):
    
    soldador = db.query(Soldador).filter(Soldador.id == id_s).first()
    if not soldador:
        raise HTTPException(404, "Soldador não encontrado.")
        
    soldador.ativo = bool(ativo)
    db.commit()
    
    acao = "soldador_ativado" if ativo else "soldador_desativado"
    registrar_auditoria(sessao.get("usuario", "?"), acao, alvo=soldador.nome)
    return RedirectResponse("/soldadores", status_code=303)