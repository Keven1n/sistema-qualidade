# 🔧 REFACTORING FASE 1: Schemas e Validação Centralizada

Esta fase implementa **Pydantic models** para validação type-safe e elimina validações manuais espalhadas.

---

## 📂 app/config.py

```python
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite:////data/dados_inspecoes.db"
    
    # Security
    secret_key: str = "troque-em-producao-use-valor-longo-aleatorio"
    encryption_key: Optional[str] = None
    
    # Session
    session_timeout_minutes: int = 60
    max_login_attempts: int = 5
    
    # Upload
    max_size_mb: int = 5
    img_dir: str = "/data/fotos"
    
    # Business Rules
    items_per_page_inspecao: int = 20
    items_per_page_auditoria: int = 30
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
```

---

## 📂 app/schemas/base.py

```python
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime

class PaginationParams(BaseModel):
    page: int = Field(1, ge=1)
    per_page: int = Field(20, ge=1, le=100)

class AuditableBase(BaseModel):
    criado_em: Optional[datetime] = None
    
    class Config:
        from_attributes = True
```

---

## 📂 app/schemas/usuario.py

```python
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime

class UsuarioBase(BaseModel):
    usuario: str = Field(..., min_length=3, max_length=50)
    nome: str = Field(..., min_length=1, max_length=100)
    papel: str = Field("inspetor")
    
    @field_validator('usuario')
    def usuario_lowercase(cls, v):
        return v.strip().lower()
    
    @field_validator('nome', 'papel')
    def strip_strings(cls, v):
        if isinstance(v, str):
            return v.strip()
        return v
    
    @field_validator('papel')
    def papel_must_be_valid(cls, v):
        if v not in {"admin", "inspetor", "visitante"}:
            raise ValueError("Papel deve ser admin, inspetor ou visitante")
        return v

class UsuarioCreate(UsuarioBase):
    senha: str = Field(..., min_length=6, max_length=100)

class UsuarioUpdate(BaseModel):
    papel: Optional[str] = None
    ativo: Optional[bool] = None
    
    @field_validator('papel')
    def papel_must_be_valid(cls, v):
        if v and v not in {"admin", "inspetor", "visitante"}:
            raise ValueError("Papel deve ser admin, inspetor ou visitante")
        return v

class UsuarioResponse(UsuarioBase):
    id: int
    ativo: bool
    criado_em: datetime
    
    class Config:
        from_attributes = True
```

---

## 📂 app/schemas/inspecao.py

```python
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime

class InspecaoBase(BaseModel):
    os: str = Field(..., min_length=1, max_length=20)
    data: str = Field(...)  # "YYYY-MM-DD"
    modelo: str = Field(..., max_length=100)
    soldador: str = Field(..., max_length=100)
    processo: str = Field(...)
    status: str = Field(...)
    defeitos: Optional[List[str]] = None
    obs: str = Field("", max_length=2500)
    
    @field_validator('os')
    def os_must_be_numeric(cls, v):
        if not v.strip().isdigit():
            raise ValueError("O.S. deve conter apenas números")
        return v.strip()
    
    @field_validator('modelo', 'soldador', 'processo', 'status')
    def max_100_chars(cls, v):
        if len(v.strip()) > 100:
            raise ValueError(f"Campo excede 100 caracteres")
        return v.strip()
    
    @field_validator('obs')
    def obs_max_2500(cls, v):
        if len(v) > 2500:
            raise ValueError("Obs excede 2500 caracteres")
        return v.strip()

class InspecaoCreate(InspecaoBase):
    assinatura_b64: Optional[str] = None
    reinspeção_de: Optional[int] = None

class InspecaoResponse(InspecaoBase):
    id: int
    fotos: Optional[str] = None
    assinatura: Optional[str] = None
    reinspeção_de: Optional[int] = None
    
    class Config:
        from_attributes = True

class InspecaoFilter(BaseModel):
    status: Optional[str] = None
    soldador: Optional[str] = None
    processo: Optional[str] = None
    data_ini: Optional[str] = None
    data_fim: Optional[str] = None
```

---

## 📂 app/schemas/soldador.py

```python
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional

class SoldadorBase(BaseModel):
    nome: str = Field(..., min_length=1, max_length=100)
    
    @field_validator('nome')
    def nome_must_be_stripped(cls, v):
        return v.strip()

class SoldadorCreate(SoldadorBase):
    pass

class SoldadorUpdate(BaseModel):
    ativo: bool

class SoldadorResponse(SoldadorBase):
    id: int
    ativo: bool
    
    class Config:
        from_attributes = True
```

---

## 📂 app/schemas/catalogo.py

```python
from pydantic import BaseModel, Field, field_validator
from typing import Optional

class CatalogoBase(BaseModel):
    linha: str = Field(..., min_length=1, max_length=100)
    modelo: str = Field(..., min_length=1, max_length=100)
    
    @field_validator('linha', 'modelo')
    def max_100_chars(cls, v):
        v = v.strip()
        if len(v) > 100:
            raise ValueError("Campo excede 100 caracteres")
        return v

class CatalogoCreate(CatalogoBase):
    pass

class CatalogoUpdate(BaseModel):
    ativo: bool

class CatalogoResponse(CatalogoBase):
    id: int
    ativo: bool
    
    class Config:
        from_attributes = True
```

---

## 📂 app/schemas/__init__.py

```python
from .usuario import UsuarioCreate, UsuarioUpdate, UsuarioResponse
from .inspecao import InspecaoCreate, InspecaoResponse, InspecaoFilter
from .soldador import SoldadorCreate, SoldadorUpdate, SoldadorResponse
from .catalogo import CatalogoCreate, CatalogoUpdate, CatalogoResponse
from .base import PaginationParams

__all__ = [
    "UsuarioCreate", "UsuarioUpdate", "UsuarioResponse",
    "InspecaoCreate", "InspecaoResponse", "InspecaoFilter",
    "SoldadorCreate", "SoldadorUpdate", "SoldadorResponse",
    "CatalogoCreate", "CatalogoUpdate", "CatalogoResponse",
    "PaginationParams",
]
```

---

## 📂 app/exceptions.py (NEW)

```python
from fastapi import HTTPException, status

class ValidationException(HTTPException):
    def __init__(self, message: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )

class NotFoundError(HTTPException):
    def __init__(self, resource: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{resource} não encontrado"
        )

class PermissionDenied(HTTPException):
    def __init__(self, message: str = "Sem permissão para esta ação"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=message
        )

class DuplicateResourceError(HTTPException):
    def __init__(self, resource: str):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"{resource} já existe"
        )

class AccountLockedError(HTTPException):
    def __init__(self, minutes: int = 15):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Conta bloqueada. Tente novamente em {minutes} minutos"
        )
```

---

## 🎯 BENEFÍCIOS FASE 1

✅ **Validação Centralizada**: Um único lugar para regras de validação  
✅ **Type Safety**: IDE autocomplete e detecção de typos  
✅ **DRY**: Sem repetição de `len()`, `strip()`, etc  
✅ **Documentação Automática**: Pydantic gera OpenAPI schema  
✅ **Reutilizável**: Schemas podem ser importados em qualquer router  
✅ **Testável**: Cada validador pode ser testado isoladamente  

---

## 🔄 USO NOS ROUTERS (DEPOIS)

### **Antes:**
```python
@router.post("/criar")
def criar_usuario(..., novo_usuario: str = Form(...), ...):
    if len(nova_senha) < 6 or len(nova_senha) > 100:
        raise HTTPException(400, "...")
    if len(novo_usuario.strip()) > 50:
        raise HTTPException(400, "...")
    ...
```

### **Depois:**
```python
@router.post("/criar")
def criar_usuario(
    request: Request,
    sessao: dict = Depends(require_admin),
    _csrf: None = Depends(verificar_csrf),
    usuario_data: UsuarioCreate = Depends(),
    db: Session = Depends(get_db_session)
):
    # usuario_data já é validado e type-safe
    service.criar_usuario(usuario_data, db)
    ...
```

---

## 📋 PRÓXIMAS PASSOS

1. ✅ Implementar `config.py`
2. ✅ Criar `schemas/` com models Pydantic
3. → **Próximo:** REFACTORING_FASE2.md (Repository Pattern)

