from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime

class UsuarioBase(BaseModel):
    usuario: str = Field(..., min_length=3, max_length=50)
    nome: str = Field(..., min_length=1, max_length=100)
    papel: str = Field("inspetor")
    
    @field_validator('usuario', mode="before")
    def usuario_lowercase(cls, v):
        if v:
            return v.strip().lower()
        return v
    
    @field_validator('nome', 'papel', mode="before")
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
    criado_em: Optional[datetime] = None
    
    class Config:
        from_attributes = True
