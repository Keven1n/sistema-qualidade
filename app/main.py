import os
import uuid
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import bcrypt
from cryptography.fernet import Fernet
from fastapi import FastAPI, Request, Form, UploadFile, File, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
import io
import csv

# ============================================================
# CONFIGURACOES
# ============================================================

DB_FILE        = os.getenv("DB_FILE",    "/data/dados_inspecoes.db")
IMG_DIR        = os.getenv("IMG_DIR",    "/data/fotos")
SECRET_KEY     = os.getenv("SECRET_KEY", "troque-em-producao-use-valor-longo-aleatorio")
ENC_KEY        = os.getenv("ENCRYPTION_KEY", None)
MAX_SIZE_MB    = int(os.getenv("MAX_SIZE_MB", 5))
MAX_TENTATIVAS = int(os.getenv("MAX_LOGIN_ATTEMPTS", 5))
TIMEOUT_MIN    = int(os.getenv("SESSION_TIMEOUT_MINUTES", 60))
HASH_LUCAS     = os.getenv("HASH_LUCAS", "")

MAGIC_BYTES    = {b'\xff\xd8\xff': "jpeg", b'\x89PNG\r\n\x1a\n': "png"}
TIPOS_OK       = set(MAGIC_BYTES.values())

fernet = Fernet(ENC_KEY.encode()) if ENC_KEY else None
Path(IMG_DIR).mkdir(parents=True, exist_ok=True)

CATALOGO = {
    "Linha Leite":      ["RA-100 - Resfriador Aberto", "MC-200 - Meia Cana", "FH-300 - Fechado Horizontal", "FV-400 - Vertical"],
    "Linha Industrial": ["IS-500 - Isotérmico", "MX-600 - Mistura", "ES-700 - Estocagem", "PR-800 - Processo"],
    "Tinas de Sorvete": ["MT-900 - Maturadora", "MG-910 - Maturadora Gás", "PT-920 - Pasteurizadora"],
}

# ============================================================
# BANCO DE DADOS
# ============================================================

def get_db():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS inspecoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT, os TEXT, modelo TEXT, soldador TEXT,
            processo TEXT, status TEXT, defeitos TEXT, obs TEXT, fotos TEXT
        );
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT UNIQUE NOT NULL, nome TEXT NOT NULL,
            hash_senha TEXT NOT NULL, ativo INTEGER DEFAULT 1,
            criado_em TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS tentativas_login (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT NOT NULL, momento TEXT NOT NULL, sucesso INTEGER DEFAULT 0
        );
    """)
    conn.commit()
    h = HASH_LUCAS.strip().strip('"\'').strip()
    # Garante que o hash começa com $2b$ mesmo que venha truncado do .env
    if h.startswith('$2b$') and len(h) >= 59:
        if not conn.execute("SELECT 1 FROM usuarios WHERE usuario='lucas'").fetchone():
            conn.execute("INSERT INTO usuarios (usuario, nome, hash_senha) VALUES (?,?,?)",
                         ("lucas", "Lucas Silva", h))
        else:
            conn.execute("UPDATE usuarios SET hash_senha=? WHERE usuario='lucas'", (h,))
        conn.commit()
    conn.close()

# ============================================================
# SESSAO
# ============================================================

serializer = URLSafeTimedSerializer(SECRET_KEY)

def criar_sessao(nome: str, demo: bool = False) -> str:
    return serializer.dumps({"nome": nome, "demo": demo, "ts": datetime.now().isoformat()})

def ler_sessao(token: str) -> Optional[dict]:
    try:
        data = serializer.loads(token, max_age=TIMEOUT_MIN * 60)
        return data
    except (BadSignature, SignatureExpired):
        return None

def get_sessao(request: Request) -> Optional[dict]:
    token = request.cookies.get("sessao")
    if not token:
        return None
    return ler_sessao(token)

def require_auth(request: Request):
    sessao = get_sessao(request)
    if not sessao:
        raise HTTPException(status_code=status.HTTP_303_SEE_OTHER,
                            headers={"Location": "/login"})
    return sessao

def require_admin(request: Request):
    sessao = require_auth(request)
    if sessao.get("demo"):
        raise HTTPException(status_code=403, detail="Acesso negado no modo demo.")
    return sessao

# ============================================================
# AUTENTICACAO
# ============================================================

def _now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def contar_tentativas(usuario: str) -> int:
    conn = get_db()
    limite = (datetime.now() - timedelta(minutes=15)).strftime("%Y-%m-%d %H:%M:%S")
    row = conn.execute(
        "SELECT COUNT(*) FROM tentativas_login WHERE usuario=? AND sucesso=0 AND momento>?",
        (usuario, limite)
    ).fetchone()
    conn.close()
    return row[0] if row else 0

def registrar_tentativa(usuario: str, sucesso: bool):
    conn = get_db()
    conn.execute("INSERT INTO tentativas_login (usuario, momento, sucesso) VALUES (?,?,?)",
                 (usuario, _now_str(), int(sucesso)))
    conn.commit()
    conn.close()

def verificar_login(usuario: str, senha: str):
    usuario = usuario.strip().lower()
    if contar_tentativas(usuario) >= MAX_TENTATIVAS:
        return None, "bloqueado"
    conn = get_db()
    row = conn.execute(
        "SELECT nome, hash_senha FROM usuarios WHERE usuario=? AND ativo=1", (usuario,)
    ).fetchone()
    conn.close()
    if row:
        try:
            if bcrypt.checkpw(senha.encode(), row["hash_senha"].encode()):
                registrar_tentativa(usuario, True)
                return row["nome"], "ok"
        except Exception:
            pass
    registrar_tentativa(usuario, False)
    return None, "invalido"

# ============================================================
# IMAGENS
# ============================================================

def get_image_type(data: bytes):
    for magic, tipo in MAGIC_BYTES.items():
        if data.startswith(magic):
            return tipo
    return None

async def salvar_imagens(files: list) -> str:
    caminhos = []
    for arq in files:
        conteudo = await arq.read()
        if not conteudo:
            continue
        if len(conteudo) > MAX_SIZE_MB * 1024 * 1024:
            continue
        tipo = get_image_type(conteudo)
        if tipo not in TIPOS_OK:
            continue
        nome = f"{uuid.uuid4()}.{tipo}"
        caminho = os.path.join(IMG_DIR, nome)
        with open(caminho, "wb") as f:
            f.write(conteudo)
        caminhos.append(caminho)
    return ";".join(caminhos)

# ============================================================
# APP
# ============================================================

app = FastAPI(title="Sistema de Qualidade - Soldagem")
app.mount("/static", StaticFiles(directory="/app/static"), name="static")
app.mount("/fotos",  StaticFiles(directory=IMG_DIR),       name="fotos")

templates = Jinja2Templates(directory="/app/templates")

@app.on_event("startup")
def startup():
    init_db()

# ============================================================
# LOGIN / LOGOUT
# ============================================================

@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request, erro: str = ""):
    return templates.TemplateResponse("login.html", {"request": request, "erro": erro})

@app.post("/login")
def login_post(request: Request, usuario: str = Form(...), senha: str = Form(...)):
    nome, status_login = verificar_login(usuario, senha)
    if status_login == "bloqueado":
        return templates.TemplateResponse("login.html", {"request": request,
            "erro": "Conta bloqueada. Tente novamente em 15 minutos."})
    elif nome:
        token = criar_sessao(nome, demo=False)
        resp = RedirectResponse("/", status_code=303)
        resp.set_cookie("sessao", token, httponly=True, samesite="lax",
                        max_age=TIMEOUT_MIN * 60)
        return resp
    return templates.TemplateResponse("login.html", {"request": request,
        "erro": "Usuário ou senha incorretos."})

@app.post("/login-demo")
def login_demo():
    token = criar_sessao("Visitante", demo=True)
    resp = RedirectResponse("/", status_code=303)
    resp.set_cookie("sessao", token, httponly=True, samesite="lax",
                    max_age=TIMEOUT_MIN * 60)
    return resp

@app.get("/logout")
def logout():
    resp = RedirectResponse("/login", status_code=303)
    resp.delete_cookie("sessao")
    return resp

# ============================================================
# DASHBOARD
# ============================================================

@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request, sessao: dict = Depends(get_sessao)):
    if not sessao:
        return RedirectResponse("/login", status_code=303)
    conn = get_db()
    rows = conn.execute("SELECT status, soldador, modelo, defeitos FROM inspecoes").fetchall()
    conn.close()

    total = len(rows)
    aprovados  = sum(1 for r in rows if r["status"] == "Aprovado")
    reprovados = sum(1 for r in rows if r["status"] == "Reprovado / Retrabalho")
    taxa_apr   = round(aprovados  / total * 100, 1) if total else 0
    taxa_repr  = round(reprovados / total * 100, 1) if total else 0

    # Dados para gráficos
    from collections import Counter
    status_chart   = dict(Counter(r["status"]   for r in rows))
    soldador_chart = dict(Counter(r["soldador"] for r in rows if r["status"] == "Reprovado / Retrabalho"))
    modelo_chart   = dict(Counter(r["modelo"]   for r in rows))
    defeitos_list  = [d.strip() for r in rows for d in (r["defeitos"] or "").split(",") if d.strip() not in ("", "N/A")]
    defeitos_chart = dict(Counter(defeitos_list).most_common(10))

    return templates.TemplateResponse("dashboard.html", {
        "request": request, "sessao": sessao,
        "total": total, "aprovados": aprovados, "reprovados": reprovados,
        "taxa_apr": taxa_apr, "taxa_repr": taxa_repr,
        "status_chart": status_chart, "soldador_chart": soldador_chart,
        "modelo_chart": modelo_chart, "defeitos_chart": defeitos_chart,
    })

# ============================================================
# NOVA INSPECAO
# ============================================================

@app.get("/nova", response_class=HTMLResponse)
def nova_page(request: Request, sessao: dict = Depends(get_sessao)):
    if not sessao:
        return RedirectResponse("/login", status_code=303)
    return templates.TemplateResponse("nova.html", {"request": request, "sessao": sessao, "catalogo": CATALOGO})

@app.post("/nova")
async def nova_post(
    request: Request,
    sessao: dict = Depends(require_admin),
    os_num: str = Form(...),
    data_inspecao: str = Form(...),
    modelo: str = Form(...),
    soldador: str = Form(...),
    processo: str = Form(...),
    status_ins: str = Form(...),
    defeitos: list[str] = Form(default=[]),
    obs: str = Form(default=""),
    fotos: list[UploadFile] = File(default=[]),
):
    obs_salva = fernet.encrypt(obs.encode()).decode() if fernet else obs
    caminhos  = await salvar_imagens(fotos)
    conn = get_db()
    conn.execute(
        "INSERT INTO inspecoes (data,os,modelo,soldador,processo,status,defeitos,obs,fotos) VALUES (?,?,?,?,?,?,?,?,?)",
        (data_inspecao, os_num.strip(), modelo, soldador, processo, status_ins,
         ", ".join(defeitos) or "N/A", obs_salva, caminhos)
    )
    conn.commit()
    conn.close()
    return RedirectResponse("/historico?ok=1", status_code=303)

# ============================================================
# HISTORICO
# ============================================================

@app.get("/historico", response_class=HTMLResponse)
def historico(request: Request, sessao: dict = Depends(get_sessao),
              pagina: int = 1, status_f: str = "", soldador_f: str = "", processo_f: str = "", ok: str = ""):
    if not sessao:
        return RedirectResponse("/login", status_code=303)

    conn = get_db()
    query  = "SELECT * FROM inspecoes WHERE 1=1"
    params = []
    if status_f:
        query += " AND status=?";   params.append(status_f)
    if soldador_f:
        query += " AND soldador=?"; params.append(soldador_f)
    if processo_f:
        query += " AND processo=?"; params.append(processo_f)
    query += " ORDER BY id DESC"

    rows     = conn.execute(query, params).fetchall()
    soldadores = [r["soldador"] for r in conn.execute("SELECT DISTINCT soldador FROM inspecoes").fetchall()]
    conn.close()

    ITENS = 20
    total_pags = max(1, (len(rows) - 1) // ITENS + 1)
    pagina     = max(1, min(pagina, total_pags))
    rows_pag   = rows[(pagina - 1) * ITENS: pagina * ITENS]

    return templates.TemplateResponse("historico.html", {
        "request": request, "sessao": sessao,
        "rows": rows_pag, "total": len(rows),
        "pagina": pagina, "total_pags": total_pags,
        "status_f": status_f, "soldador_f": soldador_f, "processo_f": processo_f,
        "soldadores": soldadores, "ok": ok,
    })

@app.get("/exportar-csv")
def exportar_csv(sessao: dict = Depends(require_auth)):
    conn = get_db()
    rows = conn.execute("SELECT id,data,os,modelo,soldador,processo,status,defeitos,obs FROM inspecoes ORDER BY id DESC").fetchall()
    conn.close()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Data", "O.S.", "Modelo", "Soldador", "Processo", "Status", "Defeitos", "Obs"])
    for r in rows:
        writer.writerow(list(r))
    output.seek(0)
    return StreamingResponse(iter([output.getvalue()]), media_type="text/csv",
                             headers={"Content-Disposition": "attachment; filename=inspecoes.csv"})

# ============================================================
# EDITAR / EXCLUIR
# ============================================================

@app.get("/editar/{id_reg}", response_class=HTMLResponse)
def editar_page(id_reg: int, request: Request, sessao: dict = Depends(require_admin)):
    conn = get_db()
    row = conn.execute("SELECT * FROM inspecoes WHERE id=?", (id_reg,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(404, "Registro não encontrado.")
    return templates.TemplateResponse("editar.html", {"request": request, "sessao": sessao, "row": row})

@app.post("/editar/{id_reg}")
def editar_post(id_reg: int, request: Request,
                sessao: dict = Depends(require_admin),
                os_num: str = Form(...), soldador: str = Form(...),
                processo: str = Form(...), status_ins: str = Form(...),
                defeitos: str = Form(default=""), obs: str = Form(default="")):
    conn = get_db()
    conn.execute(
        "UPDATE inspecoes SET os=?,soldador=?,processo=?,status=?,defeitos=?,obs=? WHERE id=?",
        (os_num.strip(), soldador.strip(), processo, status_ins, defeitos.strip(), obs, id_reg)
    )
    conn.commit()
    conn.close()
    return RedirectResponse("/historico", status_code=303)

@app.post("/excluir/{id_reg}")
def excluir(id_reg: int, sessao: dict = Depends(require_admin)):
    conn = get_db()
    conn.execute("DELETE FROM inspecoes WHERE id=?", (id_reg,))
    conn.commit()
    conn.close()
    return RedirectResponse("/historico", status_code=303)

# ============================================================
# USUARIOS
# ============================================================

@app.get("/usuarios", response_class=HTMLResponse)
def usuarios_page(request: Request, sessao: dict = Depends(require_admin)):
    conn = get_db()
    users = conn.execute("SELECT id, usuario, nome, ativo, criado_em FROM usuarios").fetchall()
    conn.close()
    return templates.TemplateResponse("usuarios.html", {"request": request, "sessao": sessao, "users": users})

@app.post("/usuarios/criar")
def criar_usuario(sessao: dict = Depends(require_admin),
                  novo_usuario: str = Form(...), novo_nome: str = Form(...),
                  nova_senha: str = Form(...)):
    if len(nova_senha) < 6:
        raise HTTPException(400, "Senha muito curta.")
    h = bcrypt.hashpw(nova_senha.encode(), bcrypt.gensalt()).decode()
    conn = get_db()
    try:
        conn.execute("INSERT INTO usuarios (usuario, nome, hash_senha) VALUES (?,?,?)",
                     (novo_usuario.strip().lower(), novo_nome.strip(), h))
        conn.commit()
    except sqlite3.IntegrityError:
        raise HTTPException(400, "Usuário já existe.")
    finally:
        conn.close()
    return RedirectResponse("/usuarios", status_code=303)

@app.post("/usuarios/{id_user}/toggle")
def toggle_usuario(id_user: int, sessao: dict = Depends(require_admin), ativo: int = Form(...)):
    conn = get_db()
    conn.execute("UPDATE usuarios SET ativo=? WHERE id=?", (ativo, id_user))
    conn.commit()
    conn.close()
    return RedirectResponse("/usuarios", status_code=303)
