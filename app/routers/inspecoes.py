import os
import uuid
import csv
import io
from datetime import datetime
from collections import Counter
from typing import Optional
from PIL import Image
import traceback

from fastapi import APIRouter, Request, Form, UploadFile, File, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse, Response
from weasyprint import HTML
from sqlalchemy.orm import Session
from sqlalchemy import desc
from cryptography.fernet import Fernet

from app.database import get_db_session
from app.models import Inspecao, Catalogo, Soldador
from app.dependencies import (
    templates, get_sessao, require_auth, require_admin, require_inspetor_ou_admin, 
    verificar_csrf, provide_inspecao_service, provide_soldador_service, provide_catalogo_service
)
from app.services.inspecao import InspecaoService
from app.services.soldador import SoldadorService
from app.services.catalogo import CatalogoService
from app.services.auditoria import registrar_auditoria

router = APIRouter(tags=["Inspeções"])

IMG_DIR = os.getenv("IMG_DIR", "/data/fotos")
ENC_KEY = os.getenv("ENCRYPTION_KEY", None)
MAX_SIZE_MB = int(os.getenv("MAX_SIZE_MB", 5))
fernet = Fernet(ENC_KEY.encode()) if ENC_KEY else None

MAGIC_BYTES = {b'\xff\xd8\xff': "jpeg", b'\x89PNG\r\n\x1a\n': "png"}
TIPOS_OK = set(MAGIC_BYTES.values())
PROCESSOS = ["TIG Manual", "TIG Orbital"]
DEFEITOS_OPCOES = ["Porosidade", "Trinca", "Falta de Fusão", "Mordedura", "Excesso de Reforço", "Oxidação"]

def get_image_type(data: bytes):
    for magic, tipo in MAGIC_BYTES.items():
        if data.startswith(magic): return tipo
    return None

async def salvar_imagens(files: list[UploadFile]) -> str:
    caminhos = []
    for arq in files:
        if not arq.filename: continue
        conteudo = await arq.read()
        if not conteudo: continue
        if len(conteudo) > MAX_SIZE_MB * 1024 * 1024:
            raise HTTPException(400, f"Arquivo {arq.filename} excede {MAX_SIZE_MB}MB.")
        tipo = get_image_type(conteudo)
        if not tipo:
            raise HTTPException(400, f"Arquivo {arq.filename} possui um formato não permitido. Apenas imagens JPEG e PNG são aceitas.")
        
        nome = f"{uuid.uuid4()}.{tipo}"
        caminho_full = os.path.join(IMG_DIR, nome)
        
        try:
            with Image.open(io.BytesIO(conteudo)) as img:
                img.save(caminho_full, format=tipo.upper())
        except Exception as e:
            with open(caminho_full, "wb") as f:
                f.write(conteudo)
        
        caminhos.append(nome)
    return ";".join(caminhos)

@router.get("/", response_class=HTMLResponse)
def dashboard(request: Request, sessao: dict = Depends(get_sessao), data_ini: str = "", data_fim: str = "", 
              service: InspecaoService = Depends(provide_inspecao_service)):
    if not sessao: return RedirectResponse("/login", status_code=303)
    
    query = service.repo.db.query(Inspecao)
    if data_ini: query = query.filter(Inspecao.data >= data_ini)
    if data_fim: query = query.filter(Inspecao.data <= data_fim)
    rows = query.all()

    stats = service.repo.get_statistics()
    total = len(rows) # Override para considerar filtros que get_statistics nao contempla
    aprovados = sum(1 for r in rows if r.status == "Aprovado")
    reprovados = sum(1 for r in rows if r.status == "Reprovado / Retrabalho")
    
    status_chart = dict(Counter(r.status for r in rows))
    soldador_chart = dict(Counter(r.soldador for r in rows if r.status == "Reprovado / Retrabalho"))
    modelo_chart = dict(Counter(r.modelo for r in rows))
    defeitos_list = [d.strip() for r in rows for d in (r.defeitos or "").split(",") if d.strip() not in ("", "N/A")]

    return templates.TemplateResponse("dashboard.html", {
        "request": request, "sessao": sessao, "total": total, "aprovados": aprovados, "reprovados": reprovados,
        "taxa_apr": round(aprovados / total * 100, 1) if total else 0, "taxa_repr": round(reprovados / total * 100, 1) if total else 0,
        "status_chart": status_chart, "soldador_chart": soldador_chart, "modelo_chart": modelo_chart, 
        "defeitos_chart": dict(Counter(defeitos_list).most_common(10)), "data_ini": data_ini, "data_fim": data_fim,
    })

@router.get("/nova", response_class=HTMLResponse)
def nova_page(request: Request, sessao: dict = Depends(require_inspetor_ou_admin), reinspeção_de: Optional[int] = None, 
              cat_service: CatalogoService = Depends(provide_catalogo_service), sold_service: SoldadorService = Depends(provide_soldador_service),
              insp_service: InspecaoService = Depends(provide_inspecao_service)):
    if not sessao: return RedirectResponse("/login", status_code=303)
    
    cat_rows = cat_service.repo.db.query(Catalogo).filter(Catalogo.ativo == True).order_by(Catalogo.linha, Catalogo.modelo).all()
    catalogo = {}
    for r in cat_rows: catalogo.setdefault(r.linha, []).append(r.modelo)
    soldadores = [s.nome for s in sold_service.repo.db.query(Soldador).filter(Soldador.ativo == True).order_by(Soldador.nome).all()]
    
    origem = insp_service.get_by_id(reinspeção_de) if reinspeção_de else None
    return templates.TemplateResponse("nova.html", {
        "request": request, "sessao": sessao, "catalogo": catalogo, "soldadores": soldadores,
        "processos": PROCESSOS, "defeitos_opcoes": DEFEITOS_OPCOES, "today": datetime.today().strftime("%Y-%m-%d"),
        "reinspeção_de": reinspeção_de, "origem": origem,
    })

@router.post("/nova")
async def nova_post(
    request: Request, sessao: dict = Depends(require_inspetor_ou_admin),
    _csrf: None = Depends(verificar_csrf),
    os_num: str = Form(...), data_inspecao: str = Form(...), modelo: str = Form(...), soldador: str = Form(...),
    processo: str = Form(...), status_ins: str = Form(...), defeitos: list[str] = Form(default=[]),
    obs: str = Form(default=""), fotos: list[UploadFile] = File(default=[]), assinatura_b64: str = Form(default=""), reinspeção_de: Optional[int] = Form(default=None),
    service: InspecaoService = Depends(provide_inspecao_service)
):
    from app.schemas.inspecao import InspecaoCreate
    try:
        # Validação com Pydantic Schema!
        dados = InspecaoCreate(
            os=os_num, data=data_inspecao, modelo=modelo, soldador=soldador,
            processo=processo, status=status_ins, defeitos=defeitos, obs=obs,
            assinatura_b64=assinatura_b64, reinspeção_de=reinspeção_de
        ).model_dump()
    except ValueError as e:
        raise HTTPException(400, str(e))

    if not reinspeção_de:
        duplicada = service.repo.db.query(Inspecao).filter(Inspecao.os == dados['os'], Inspecao.reinspeção_de == None).first()
        if duplicada:
            return RedirectResponse(f"/nova?erro=O.S. {dados['os']} já está registrada.", status_code=303)

    caminhos = await salvar_imagens(fotos)
    
    assinatura_path = None
    if assinatura_b64:
        if not assinatura_b64.startswith("data:image/png;base64,"):
            raise HTTPException(400, "Assinatura possui formato inválido.")
        if len(assinatura_b64) > 1_000_000:
            raise HTTPException(400, "Assinatura muito grande.")
            
        import base64
        b64_data = assinatura_b64.split(",")[1]
        nome_ass = f"ass_{uuid.uuid4()}.png"
        with open(os.path.join(IMG_DIR, nome_ass), "wb") as f:
            f.write(base64.b64decode(b64_data))
        assinatura_path = nome_ass

    # Delegação para a Criação pelo Service (Remove campos que o modelo do banco não conhece)
    dict_banco = {
        "os": dados["os"],
        "data": dados["data"],
        "modelo": dados["modelo"],
        "soldador": dados["soldador"],
        "processo": dados["processo"],
        "status": dados["status"],
        "defeitos": ", ".join(dados["defeitos"]) if dados["defeitos"] else "N/A",
        "obs": fernet.encrypt(dados["obs"].encode()).decode() if fernet else dados["obs"],
        "fotos": caminhos,
        "assinatura": assinatura_path,
        "reinspeção_de": dados["reinspeção_de"]
    }

    service.criar_inspecao(dict_banco, sessao.get("usuario", "?"))

    return RedirectResponse("/historico?ok=1", status_code=303)

@router.get("/historico", response_class=HTMLResponse)
def historico(request: Request, sessao: dict = Depends(get_sessao), pagina: int = 1, status_f: str = "", 
              soldador_f: str = "", processo_f: str = "", data_ini: str = "", data_fim: str = "", ok: str = "", 
              service: InspecaoService = Depends(provide_inspecao_service), sold_service: SoldadorService = Depends(provide_soldador_service)):
    if not sessao: return RedirectResponse("/login", status_code=303)

    query = service.repo.db.query(Inspecao)
    if status_f: query = query.filter(Inspecao.status == status_f)
    if soldador_f: query = query.filter(Inspecao.soldador == soldador_f)
    if processo_f: query = query.filter(Inspecao.processo == processo_f)
    if data_ini: query = query.filter(Inspecao.data >= data_ini)
    if data_fim: query = query.filter(Inspecao.data <= data_fim)

    total = query.count()
    ITENS = 20
    total_pags = max(1, (total - 1) // ITENS + 1)
    pagina = max(1, min(pagina, total_pags))
    
    rows = query.order_by(desc(Inspecao.id)).offset((pagina - 1) * ITENS).limit(ITENS).all()
    soldadores = [s.nome for s in sold_service.repo.db.query(Soldador).filter(Soldador.ativo == True).order_by(Soldador.nome).all()]

    return templates.TemplateResponse("historico.html", {
        "request": request, "sessao": sessao, "rows": rows, "total": total, "pagina": pagina, "total_pags": total_pags, 
        "soldadores": soldadores, "ok": ok,
    })

@router.get("/historico/{id_reg}/pdf", response_class=Response)
def exportar_pdf(id_reg: int, request: Request, sessao: dict = Depends(get_sessao), service: InspecaoService = Depends(provide_inspecao_service)):
    if not sessao: return RedirectResponse("/login", status_code=303)
    
    row = service.get_by_id(id_reg)
    
    html_content = templates.get_template("relatorio_pdf.html").render({
        "row": row, "data_hoje": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    })
    
    try:
        pdf_bytes = HTML(string=html_content, base_url="file:///").write_pdf()
    except Exception as e:
        return Response(content="ERRO NO WEASYPRINT:\n" + traceback.format_exc(), status_code=500, media_type="text/plain")
    
    registrar_auditoria(service.db, sessao.get("usuario", "?"), "exportou_pdf", alvo=f"inspecao#{id_reg}", detalhe=f"O.S: {row.os}")
    service.db.commit()
    
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="ThermoLac_Laudo_OS_{row.os}.pdf"'}
    )

@router.post("/dashboard/exportar-pdf", response_class=Response)
def exportar_dashboard_dossie(
    request: Request,
    sessao: dict = Depends(get_sessao),
    _csrf: None = Depends(verificar_csrf),
    service: InspecaoService = Depends(provide_inspecao_service),
    data_ini: str = Form(""), data_fim: str = Form(""),
    c_status: str = Form(""), c_soldador: str = Form(""),
    c_modelo: str = Form(""), c_defeitos: str = Form("")
):
    if not sessao: return RedirectResponse("/login", status_code=303)
    
    query = service.repo.db.query(Inspecao)
    if data_ini: query = query.filter(Inspecao.data >= data_ini)
    if data_fim: query = query.filter(Inspecao.data <= data_fim)
    rows = query.all()

    total = len(rows)
    aprovados = sum(1 for r in rows if r.status == "Aprovado")
    reprovados = sum(1 for r in rows if r.status == "Reprovado / Retrabalho")
    taxa_apr = round(aprovados / total * 100, 1) if total else 0
    taxa_repr = round(reprovados / total * 100, 1) if total else 0

    per = f"De {data_ini} a {data_fim}" if (data_ini and data_fim) else (f"A partir de {data_ini}" if data_ini else (f"Até {data_fim}" if data_fim else "Todo o Período"))

    html_content = templates.get_template("dossie_pdf.html").render({
        "data_hoje": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "periodo": per, "total": total, "aprovados": aprovados, "reprovados": reprovados, 
        "taxa_apr": taxa_apr, "taxa_repr": taxa_repr,
        "c_status": c_status, "c_soldador": c_soldador, "c_modelo": c_modelo, "c_defeitos": c_defeitos
    })
    
    pdf_bytes = HTML(string=html_content, base_url="file:///").write_pdf()
    registrar_auditoria(service.db, sessao.get("usuario", "?"), "exportou_dossie")
    service.db.commit()
    
    return Response(
        content=pdf_bytes, media_type="application/pdf", headers={"Content-Disposition": 'attachment; filename="ThermoLac_Dossie_Mensal.pdf"'}
    )

@router.get("/exportar-csv")
def exportar_csv(request: Request, sessao: dict = Depends(require_auth), data_ini: str = "", data_fim: str = "", service: InspecaoService = Depends(provide_inspecao_service)):
    query = service.repo.db.query(Inspecao).order_by(desc(Inspecao.id))
    if data_ini: query = query.filter(Inspecao.data >= data_ini)
    if data_fim: query = query.filter(Inspecao.data <= data_fim)
    rows = query.all()
    
    registrar_auditoria(service.db, sessao.get("usuario", "?"), "exportou_csv")
    service.db.commit()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Data", "O.S.", "Modelo", "Soldador", "Processo", "Status", "Defeitos", "Obs", "Assinatura", "Reinspeção de"])
    for r in rows: writer.writerow([r.id, r.data, r.os, r.modelo, r.soldador, r.processo, r.status, r.defeitos, r.obs, "Sim" if r.assinatura else "Não", r.reinspeção_de])
    output.seek(0)
    return StreamingResponse(iter([output.getvalue()]), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=inspecoes.csv"})

@router.get("/editar/{id_reg}", response_class=HTMLResponse)
def editar_page(id_reg: int, request: Request, sessao: dict = Depends(require_admin), service: InspecaoService = Depends(provide_inspecao_service), sol_service: SoldadorService = Depends(provide_soldador_service)):
    row = service.get_by_id(id_reg)
    soldadores = [s.nome for s in sol_service.repo.db.query(Soldador).filter(Soldador.ativo == True).order_by(Soldador.nome).all()]
    return templates.TemplateResponse("editar.html", {"request": request, "sessao": sessao, "row": row, "soldadores": soldadores, "processos": PROCESSOS})

@router.post("/editar/{id_reg}")
def editar_post(id_reg: int, request: Request, sessao: dict = Depends(require_admin), _csrf: None = Depends(verificar_csrf),
                os_num: str = Form(...), soldador: str = Form(...),
                processo: str = Form(...), status_ins: str = Form(...), defeitos: str = Form(default=""), obs: str = Form(default=""), service: InspecaoService = Depends(provide_inspecao_service)):
    
    from app.schemas.inspecao import InspecaoCreate
    try:
        dados = InspecaoCreate(
            os=os_num, data="2000-01-01", modelo="bypass", soldador=soldador,
            processo=processo, status=status_ins, defeitos=[defeitos] if defeitos else [], obs=obs
        ).model_dump()
    except ValueError as e:
        raise HTTPException(400, str(e))

    row = service.get_by_id(id_reg)
    
    antes = f"os={row.os} soldador={row.soldador} status={row.status}"
    
    # Faz update manual
    row.os, row.soldador, row.processo, row.status, row.defeitos, row.obs = dados["os"], dados["soldador"], dados["processo"], dados["status"], defeitos.strip(), dados["obs"]
    service.db.commit()
    
    registrar_auditoria(service.db, sessao.get("usuario", "?"), "inspecao_editada", alvo=f"inspecao#{id_reg}", detalhe=f"antes: {antes}")
    service.db.commit()
    return RedirectResponse("/historico", status_code=303)

@router.post("/excluir/{id_reg}")
def excluir(id_reg: int, request: Request, sessao: dict = Depends(require_admin), _csrf: None = Depends(verificar_csrf), service: InspecaoService = Depends(provide_inspecao_service)):
    row = service.get_by_id(id_reg)
    
    service.delete(id_reg) # Deleta e commita!
    
    registrar_auditoria(service.db, sessao.get("usuario", "?"), "inspecao_excluida", alvo=f"inspecao#{id_reg}", detalhe=f"os={row.os} status={row.status}")
    service.db.commit()
    
    return RedirectResponse("/historico", status_code=303)