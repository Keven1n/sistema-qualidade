from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc
import io
import csv

from app.database import get_db_session
from app.models import Auditoria
from app.dependencies import templates, require_admin, registrar_auditoria

router = APIRouter(tags=["Auditoria"])

@router.get("/auditoria", response_class=HTMLResponse)
def auditoria_page(request: Request, sessao: dict = Depends(require_admin),
                   pagina: int = 1, usuario_f: str = "", acao_f: str = "", db: Session = Depends(get_db_session)):
    
    query = db.query(Auditoria)
    if usuario_f:
        query = query.filter(Auditoria.usuario == usuario_f)
    if acao_f:
        query = query.filter(Auditoria.acao.ilike(f"%{acao_f}%"))
    
    total = query.count()
    ITENS = 30
    total_pags = max(1, (total - 1) // ITENS + 1)
    pagina = max(1, min(pagina, total_pags))
    
    rows = query.order_by(desc(Auditoria.id)).offset((pagina - 1) * ITENS).limit(ITENS).all()
    
    usuarios_distintos = db.query(Auditoria.usuario).distinct().order_by(Auditoria.usuario).all()
    usuarios = [u[0] for u in usuarios_distintos]

    return templates.TemplateResponse("auditoria.html", {
        "request": request, "sessao": sessao,
        "rows": rows, "total": total,
        "pagina": pagina, "total_pags": total_pags,
        "usuario_f": usuario_f, "acao_f": acao_f,
        "usuarios": usuarios,
    })

@router.get("/exportar-auditoria")
def exportar_auditoria(request: Request, sessao: dict = Depends(require_admin), db: Session = Depends(get_db_session)):
    rows = db.query(Auditoria).order_by(desc(Auditoria.id)).all()
    registrar_auditoria(sessao.get("usuario", "?"), "exportou_auditoria")
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Momento", "Usuário", "Ação", "Alvo", "Detalhe"])
    for r in rows:
        writer.writerow([r.id, r.momento, r.usuario, r.acao, r.alvo, r.detalhe])
    output.seek(0)
    return StreamingResponse(iter([output.getvalue()]), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=auditoria.csv"})