from pydantic import BaseModel, Field, field_validator
from typing import Optional

class SoldadorBase(BaseModel):
    nome: str = Field(..., min_length=1, max_length=100)
    
    @field_validator('nome', mode='before')
    def nome_must_be_stripped(cls, v):
        if isinstance(v, str):
            return v.strip()
        return v

class SoldadorCreate(SoldadorBase):
    pass

class SoldadorUpdate(BaseModel):
    ativo: bool

class SoldadorResponse(SoldadorBase):
    id: int
    ativo: bool
    
    class Config:
        from_attributes = True
