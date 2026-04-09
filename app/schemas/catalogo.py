from pydantic import BaseModel, Field, field_validator
from typing import Optional

class CatalogoBase(BaseModel):
    linha: str = Field(..., min_length=1, max_length=100)
    modelo: str = Field(..., min_length=1, max_length=100)
    
    @field_validator('linha', 'modelo', mode='before')
    def strip_strings(cls, v):
        if isinstance(v, str):
            v_str = v.strip()
            if len(v_str) > 100:
                raise ValueError("Campo excede 100 caracteres")
            return v_str
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
