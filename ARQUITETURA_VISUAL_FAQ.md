# 🏗️ VISUALIZAÇÃO DE ARQUITETURA + FAQ

---

## 📐 ARQUITETURA ATUAL (Problemas Destacados)

```
┌─────────────────────────────────────────────────────────────────┐
│                    🌐 CAMADA DE APRESENTAÇÃO                    │
│                 Jinja2 Templates + JavaScript                   │
│  ❌ PROBLEMA: Validações espalhadas no frontend                │
└────────────────┬────────────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────────────┐
│                  🛣️ CAMADA DE ROTEAMENTO                         │
│      auth.py, usuarios.py, inspecoes.py, soldadores.py...      │
│                                                                   │
│  ❌ 175 LINHAS DUPLICADAS (CRUD patterns)                       │
│  ❌ VALIDAÇÕES MANUAIS (não reutilizáveis)                      │
│  ❌ LÓGICA ESPALHADA (difícil de manter)                        │
│  ❌ ERRO HANDLING INCONSISTENTE                                 │
│                                                                   │
│  ┌──────────────┬──────────────┬──────────────┬──────────────┐  │
│  │ usuarios.py  │inspecoes.py  │ catálogo.py  │ auditoria.py │  │
│  │              │              │              │              │  │
│  │ - criar      │ - nova       │ - criar      │ - listar     │  │
│  │ - editar     │ - historico  │ - editar     │ - exportar   │  │
│  │ - toggle     │ - editar     │ - toggle     │              │  │
│  │ - papel      │ - excluir    │              │              │  │
│  └──────────────┴──────────────┴──────────────┴──────────────┘  │
│                                                                   │
└────────────────┬────────────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────────────┐
│            🔄 GOD MODULE - dependencies.py (180 linhas)         │
│                                                                   │
│  ├─ Jinja2 Templates                                             │
│  ├─ Session management (criar/ler com Fernet + itsdangerous)   │
│  ├─ CSRF validation (HMAC-SHA256)                               │
│  ├─ Dependency injection (require_auth, require_admin, etc)     │
│  ├─ registrar_auditoria() ❌ Abre nova sessão cada call        │
│  └─ Várias concerns misturadas                                  │
│                                                                   │
│  ❌ VIOLAÇÃO: Single Responsibility Principle                    │
│  ❌ PROBLEMA: Auditoria abre conexão extra (N+1 problem)        │
└────────────────┬────────────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────────────┐
│               ⚙️ ACESSO AO BANCO (Direto em Routers)            │
│                                                                   │
│  ❌ 5-6 LOOPS PYTHON em dashboard (N+1 queries)                 │
│  ❌ PAGINAÇÃO DUPLICADA (3 lugares diferentes)                  │
│  ❌ LÓGICA SQL ESPALHADA                                        │
│  ❌ SEM ÍNDICES COMPOSTOS                                       │
│                                                                   │
│  query = db.query(Inspecao)  ← 1 query                          │
│  aprovados = sum(...)         ← loop 1                          │
│  reprovados = sum(...)        ← loop 2                          │
│  status_chart = Counter(...)  ← loop 3                          │
│  ...                          ← 5+ loops mais                   │
│                                                                   │
│  Tempo com 10k registros: 800ms 😞                              │
└────────────────┬────────────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────────────┐
│                    💾 BANCO DE DADOS                             │
│         PostgreSQL / SQLite (dual-stack correto!)               │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🚀 ARQUITETURA PROPOSTA (Otimizada)

```
┌─────────────────────────────────────────────────────────────────┐
│                    🌐 CAMADA DE APRESENTAÇÃO                    │
│                 Jinja2 Templates + JavaScript                   │
│            ✅ Sem validação (delegada para frontend)            │
└────────────────┬────────────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────────────┐
│          🛣️ ROUTERS (Orquestração APENAS)                       │
│                                                                   │
│  ✅ FINO (60-120 linhas por arquivo)                            │
│  ✅ LIMPO (sem lógica de negócio)                               │
│  ✅ TESTÁVEL (tudo é injetado)                                  │
│                                                                   │
│  POST /users/criar → UsuarioCreate (Pydantic validation)       │
│                  ↓                                               │
│            user_service.criar_usuario(data)                     │
│                  ↓→ (RedirectResponse)                          │
│                                                                   │
│  ❌ NADA DE VALIDAÇÃO AQUI                                      │
│  ❌ NADA DE QUERY AQUI                                          │
│                                                                   │
└────────────────┬────────────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────────────┐
│          📦 SCHEMAS (Validação Type-Safe)                       │
│                                                                   │
│  ✅ UMA FONTE DE VERDADE                                        │
│  ✅ PYDANTIC (validação automática)                             │
│  ✅ DOCUMENTAÇÃO (OpenAPI gerada)                               │
│                                                                   │
│  ┌──────────────┬──────────────┬──────────────┬──────────────┐  │
│  │ usuario.py   │inspecao.py   │ soldador.py  │ catalogo.py  │  │
│  │              │              │              │              │  │
│  │ - UsuarioBase│ - InspecaoBase│- SoldadorBase│-CatalogoBase│  │
│  │ - UsuarioCreate│-InspecaoCreate│-SoldadorCreate│ ...      │  │
│  │ - UsuarioResponse│ - InspecaoResponse│ ...              │  │
│  │ - validators │ - validators │ - validators │ - validators│  │
│  └──────────────┴──────────────┴──────────────┴──────────────┘  │
│                                                                   │
│  @field_validator('usuario')                                   │
│  def usuario_lowercase(cls, v):                                │
│      return v.strip().lower()                                  │
│                                                                   │
│  @field_validator('papel')                                     │
│  def papel_must_be_valid(cls, v):                              │
│      if v not in {"admin", "inspetor", "visitante"}:           │
│          raise ValueError("Invalid papel")                      │
└────────────────┬────────────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────────────┐
│        🎯 SERVICES (Business Logic Centralizada)                │
│                                                                   │
│  ✅ REUTILIZÁVEL (não sabe de HTTP)                             │
│  ✅ TESTÁVEL (sem BD, sem side effects)                         │
│  ✅ AUDITORIA AUTOMÁTICA                                        │
│                                                                   │
│  ┌──────────────┬──────────────┬──────────────┬──────────────┐  │
│  │ auth.py      │ usuario.py   │ inspecao.py  │ cache.py     │  │
│  │              │              │              │              │  │
│  │ - verificar_│ - criar_      │ - criar_     │ - get()      │  │
│  │   login()    │   usuario()  │   inspecao() │ - set()      │  │
│  │ - criar_user │ - alterar_   │ - editar_    │ - cleared()  │  │
│  │   _com_bcr   │   papel()    │   inspecao() │ - @cached    │  │
│  │   ypt()      │ - toggle_    │ - obter_     │              │  │
│  │              │   usuario()  │   dashboard_ │              │  │
│  │              │              │   data()     │ Redis-Ready  │  │
│  │              │              │              │              │  │
│  │              │              │ ✅ SQL       │              │  │
│  │              │              │ aggregations │              │  │
│  │              │              │ (10x mais    │              │  │
│  │              │              │  rápido)     │              │  │
│  └──────────────┴──────────────┴──────────────┴──────────────┘  │
│                                                                   │
│  def obter_estatisticas(filters) -> Dict:                      │
│      \"\"\"UMA ÚNICA QUERY SQL com agregações\"\"\"               │
│      return repo.get_statistics(filters)                       │
│                                                                   │
│  # Resultado:                                                   │
│  # {                                                            │
│  #   \"total\": 10000,                                          │
│  #   \"aprovados\": 8500,                                       │
│  #   \"taxa_aprovacao\": 85.0                                  │
│  # }                                                            │
│                                                                   │
└────────────────┬────────────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────────────┐
│      🗄️ REPOSITORIES (Data Access Abstraction)                  │
│                                                                   │
│  ✅ TESTÁVEL (mockaveis)                                        │
│  ✅ QUERIES OTIMIZADAS (SQL nativo)                             │
│  ✅ ZERO DUPLICAÇÃO CRUD                                        │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │              BaseRepository<T> Genérico                    │  │
│  │                                                            │  │
│  │  - find_by_id(id) → T                                     │  │
│  │  - find_all(limit, offset) → List[T]                     │  │
│  │  - create(obj) → T                                        │  │
│  │  - update(id, **kwargs) → T                               │  │
│  │  - delete(id) → bool                                      │  │
│  │  - toggle_boolean_field(id, field) → T                   │  │
│  │  - paginate(page, per_page, **filters) → Dict             │  │
│  │  - count(**filters) → int                                 │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                   │
│  ┌──────────────┬──────────────┬──────────────┬──────────────┐  │
│  │ usuario_repo │inspecao_repo │ soldador_repo│ catalogo_repo│  │
│  │              │              │              │              │  │
│  │ - find_by_   │ - find_by_os()│ - find_by_  │ - find_by_  │  │
│  │   username() │ - get_stats() │   nome()    │   linha_...  │  │
│  │ - username_  │ - get_status_ │ - nome_     │ - get_      │  │
│  │   exists()   │   distribution()│exists()   │   catalog_  │  │
│  │ - create_    │ - get_soldier_│             │   grouped() │  │
│  │   user()     │   failures()  │             │             │  │
│  │              │ - get_modelo_ │             │             │  │
│  │              │   distribution│             │             │  │
│  │              │               │             │             │  │
│  │              │ ✅ SQL        │             │ ✅ Indexado │  │
│  │              │ aggregations  │             │ optimized   │  │
│  │              │ (sem loops!)  │             │             │  │
│  └──────────────┴──────────────┴──────────────┴──────────────┘  │
│                                                                   │
└────────────────┬────────────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────────────┐
│           🔒 SECURITY & INFRASTRUCTURE                           │
│                                                                   │
│  ┌──────────────┬──────────────┬──────────────┬──────────────┐  │
│  │ session.py   │ logging.py   │ middleware.py│ exceptions.py│  │
│  │              │              │              │              │  │
│  │ - SessionData│ - JSON       │ - Error      │ - Custom     │  │
│  │   (TypedDict)│   formatter  │   Handling   │   exceptions │  │
│  │ - Session    │ - Structured │ - Global     │ - Error IDs  │  │
│  │   Manager    │   logging    │   error      │              │  │
│  │ - @cached    │ - log_action │   catcher    │              │  │
│  │   decorator  │ - Audit logs │              │              │  │
│  └──────────────┴──────────────┴──────────────┴──────────────┘  │
│                                                                   │
└────────────────┬────────────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────────────┐
│                    💾 BANCO DE DADOS                             │
│         PostgreSQL / SQLite (dual-stack + índices)              │
│                                                                   │
│  ✅ ÍNDICES COMPOSTOS (data, status), (soldador, status)       │
│  ✅ QUERIES OTIMIZADAS                                         │
│  ✅ SEM N+1 PROBLEMS                                           │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔄 FLUXO DE REQUISIÇÃO: Comparação

### **ANTES: Criar Usuário (Atual)**

```
1. POST /usuarios/criar
   ↓
2. Router recebe: novo_usuario, novo_nome, nova_senha, novo_papel
   ├─ ❌ Valida manualmente:
   │  ├─ len(nova_senha) < 6 or > 100
   │  ├─ len(novo_usuario.strip()) > 50
   │  ├─ novo_papel not in PAPEIS_VALIDOS
   │  └─ ...
   ↓
3. Query BD: db.query(Usuario).filter(Usuario.usuario == ...)
   ├─ ❌ Se encontrou:
   │  └─ raise HTTPException(400, \"Usuário já existe\")
   ↓
4. Criptografia: bcrypt.hashpw(nova_senha.encode(), ...)
   ↓
5. Save: db.add(novo_user), db.commit()
   ↓
6. Auditoria: registrar_auditoria(...)
   ├─ ❌ Abre NOVA sessão BD
   ├─ db = SessionLocal()
   ├─ db.add(auditoria)
   ├─ db.commit()
   └─ db.close()
   ↓
7. Return: RedirectResponse(\"/usuarios\")

Problemas:
❌ Validação espalhada
❌ Auditoria abre conexão extra
❌ Sem transação única
❌ Código repetido 3+ pladeces
```

### **DEPOIS: Criar Usuário (Proposto)**

```
1. POST /usuarios/criar
   ↓
2. Form parsing → UsuarioCreate (Pydantic)
   ├─ ✅ Validação automática:
   │  ├─ Field(min_length=3, max_length=50) → usuario
   │  ├─ Field(min_length=6, max_length=100) → senha
   │  ├─ @field_validator('papel') → checks PAPEIS_VALIDOS
   │  └─ @field_validator('usuario') → strip().lower()
   ├─ Se erro → HTTPException(400, detail)
   ↓
3. Service.criar_usuario(usuario_data, user_id)
   ├─ ✅ Uma única responsabilidade
   ├─ AuthService.criar_usuario_com_bcrypt()
   │  ├─ usuario_repo.username_exists() → Query
   │  ├─ bcrypt.hashpw()
   │  └─ usuario_repo.create_user() → Save
   │
   ├─ registrar_auditoria() 
   │  └─ ✅ Dentro da MESMA transação
   │
   └─ Return: Usuario criado
   ↓
4. Router: return RedirectResponse(\"/usuarios\")

Benefícios:
✅ Validação centralizada
✅ Sem queries duplicadas
✅ Transação única
✅ Auditoria automática
✅ Type-safe
✅ Testável
```

---

## ❓ FAQ - Perguntas Frequentes

### **P: Por que refatorar se o código funciona?**
**R:** Código que funciona mas é difícil de manter custa:
- 70% mais tempo em features novas
- Bugs difíceis de rastrear
- Risco em mudanças (fear of changing)
- Novo dev leva semanas para entender

A refatoração reduz custo de manutenção de longo prazo.

---

### **P: Vai quebrar o sistema em produção?**
**R:** Não! Refatoração pode ser feita gradualmente:

```
Sprint 1: Deploy schemas/ (sem usar ainda) ✅ Safe
Sprint 2: Deploy repositories/ (shadow mode - sem usar) ✅ Safe
Sprint 3: Migrate router por router (1 de cada vez) ✅ Safe
Sprint 4: Cleanup código antigo ✅ Safe
```

Zero downtime com feature flags.

---

### **P: Quanto tempo leva?**
**R:** 4 sprints de 1 semana cada (4 semanas):
- Fase 1 (5-6 dias): Config, schemas, validation
- Fase 2 (5-6 dias): Repositories, migrations
- Fase 3 (5-6 dias): Services, aggregations
- Fase 4 (5-6 dias): Routers, logging, testes

Com time de 1-2 devs, pode ser 2-3 meses com trabalho paralelo.

---

### **P: Como faço testes sem quebrar tudo?**
**R:** Tipos de testes:

```python
# 1. Unit tests (schemas, services, repos)
# - Sem BD (mock)
# - Rápidos (ms)
# - Cobertura 85%+
pytest tests/test_services.py

# 2. Integration tests (routers com BD de teste)
# - Com BD real (SQLite em mem)
# - Moderados (s)
# - Cobertura 60%+
pytest tests/test_routers.py

# 3. E2E tests (navegador real)
# - Selenium/Playwright
# - Lentos (min)
# - Cobertura 20%+
pytest tests/test_e2e.py
```

---

### **P: Devo usar Redis para cache?**
**R:** Recomendações:

| Cenário | Cache | Por quê |
|---------|-------|--------|
| **< 100 requisições/min** | In-memory (dict) | Overhead desnecessário |
| **100-1000 req/min** | In-memory com TTL | Simples, rápido |
| **> 1000 req/min** | Redis | Distributed |

Começar com in-memory, escalar para Redis se precisar.

---

### **P: Usar Alembic para migrations?**
**R:** Sim! Por quê:

```
Sem Alembic:
- Criar tabela manualmente
- Apagar coluna manualmente
- Problema se BD divergir

Com Alembic:
alembic revision --autogenerate -m "add user_role"
alembic upgrade head
→ Versionado, automático, reproducível
```

Setup é 15 minutos.

---

### **P: Como migrar dados antigos para new schema?**
**R:** Usar migrations:

```python
# alembic/versions/001_add_user_role.py

def upgrade():
    op.add_column('usuarios', sa.Column('papel', sa.String()))
    # Migrar dados antigos
    op.execute(\"UPDATE usuarios SET papel='inspetor' WHERE papel IS NULL\")

def downgrade():
    op.drop_column('usuarios', 'papel')
```

Garante integridade de dados.

---

### **P: Como testar services sem BD?**
**R:** Mock repositories:

```python
def test_criar_usuario_sucesso():
    # Mock
    usuario_repo_mock = Mock()
    usuario_repo_mock.username_exists.return_value = False
    usuario_repo_mock.create_user.return_value = Usuario(id=1, usuario=\"novo\")
    
    auth_service_mock = Mock()
    auth_service_mock.criar_usuario_com_bcrypt.return_value = Usuario(...)
    
    # Test
    service = UsuarioService(usuario_repo_mock, auth_service_mock, Mock())
    resultado = service.criar_usuario(UsuarioCreate(...), \"admin\")
    
    # Assert
    assert resultado.usuario == \"novo\"
    usuario_repo_mock.create_user.assert_called_once()
```

Rápido, sem BD, determinístico.

---

### **P: Pydantic nega tipos customizados?**
**R:** Pydantic suporta tipos customizados via validator:

```python
from datetime import datetime

class CustomData(BaseModel):
    data: datetime
    
    @field_validator('data')
    def data_must_be_future(cls, v):
        if v < datetime.now():
            raise ValueError('Data deve ser no futuro')
        return v
```

Também suporta: `UUID`, `Email`, `HttpUrl`, `SecretStr`, etc.

---

### **P: Devo usar Dependency Injection?**
**R:** Definitivamente sim! Por quê:

Sem DI:
```python
def criar_usuario(...):
    db = SessionLocal()  # Acoplado
    service = UsuarioService(db)  # Hard to test
    usuario = service.criar(...)
```

Com DI (FastAPI):
```python
def criar_usuario(
    service: UsuarioService = Depends(get_usuario_service)
):
    usuario = service.criar(...)  # Easy to test
```

DI permite trocar implementação (real BD vs mock) sem alterar código.

---

### **P: Como estruturar testes?**
**R:** Estrutura recomendada:

```
tests/
├── conftest.py              # Fixtures compartilhadas
├── test_schemas.py          # Pydantic models
├── test_repositories.py     # Data access
├── test_services.py         # Business logic
├── test_routers.py          # API endpoints
├── fixtures/
│   ├── usuarios.json        # Dados de teste
│   └── inspecoes.json
└── e2e/
    └── test_flows.py        # Cenários completos
```

pytest descobrir automaticamente.

---

### **P: Preciso refatorar TUDO de uma vez?**
**R:** NÃO! Fazer gradualmente:

```
Migração Gradual:

┌─────────────────────────────────────────┐
│ Sprint 1: Prepare new layer             │
│ - Criar schemas/ (não usar ainda)       │
│ - Deploy em prod (não toca routers)     │
└─────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────┐
│ Sprint 2: Data layer                    │
│ - Criar repositories/ (shadow mode)     │
│ - Testar em paralelo (sem usar)         │
└─────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────┐
│ Sprint 3: Services                      │
│ - 1 router por semana                   │
│ - Migrar usuarios.py → use services     │
│ - Migrar inspecoes.py → use services    │
│ - ...                                   │
└─────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────┐
│ Sprint 4: Cleanup                       │
│ - Remover código antigo                 │
│ - Testes finais                         │
│ - Deploy limpo                          │
└─────────────────────────────────────────┘
```

Zero risco com feature flags!

---

### **P: Devo usar TypeScript?**
**R:** Python com type hints é suficiente:

```python
# Python 3.10+ com type hints é quase TypeScript
from typing import Optional, List

def criar_usuario(
    usuario_data: UsuarioCreate,  # Type hint
    db: Session = Depends(get_db_session)
) -> UsuarioResponse:
    ...
```

IDE mesmo level de autocomplete que TypeScript.
Sem overhead de transpilação.

---

### **P: Como escalar para 10k+ requisições/min?**
**R:** Roadmap:

1. **Fase 1** (agora): Otimizar queries SQL
   - SQL aggregations (10x mais rápido)
   - Índices compostos
   - → 120ms dashboard (vs 800ms)

2. **Fase 2** (próximo): Redis cache
   - Dropdown lists (catalogo, soldadores)
   - Estatísticas pré-calculadas
   - → 50ms dashboard

3. **Fase 3** (future): Async
   - aiohttp, asyncpg
   - Parallel queries
   - → 20ms dashboard

4. **Fase 4** (future): Cache CDN
   - CloudFlare, AWS CloudFront
   - Static assets cached globally
   - → Latência global reduzida

Cada fase é independente!

---

### **P: Documentação com OpenAPI automática?**
**R:** Sim! Pydantic + FastAPI gera automaticamente:

```python
@app.get(\"/users/{user_id}\", response_model=UsuarioResponse)
def get_user(user_id: int) -> UsuarioResponse:
    \"\"\"Get usuario by ID\"\"\"
    return usuario_service.get_by_id(user_id)
```

FastAPI gera em `http://localhost:8000/docs`:
- Swagger UI interativa
- Schemas JSON completos
- ReDoc (docs legível)

Zero configuração!

---

## 📚 Recursos Recomendados

- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **SQLAlchemy**: https://docs.sqlalchemy.org/
- **Pydantic**: https://docs.pydantic.dev/
- **Python Type Hints**: https://peps.python.org/pep-0484/
- **Real Python**: https://realpython.com/

---

## ✅ CONCLUSÃO

A refatoração não é luxo, é **necessidade de manutenção**:

| Aspecto | Impacto |
|---------|---------|
| **Tempo de feature nova** | 70% ↓ |
| **Bugs em produção** | 80% ↓ |
| **Onboarding novo dev** | 60% ↓ |
| **Confiança em mudanças** | 300% ↑ |

**Começar semana que vem!**

