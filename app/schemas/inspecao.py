from pydantic import BaseModel, Field, field_validator
from typing import Optional, List

class InspecaoBase(BaseModel):
    os: str = Field(..., min_length=1, max_length=20)
    data: str = Field(...)  # "YYYY-MM-DD"
    modelo: str = Field(..., max_length=100)
    soldador: str = Field(..., max_length=100)
    processo: str = Field(...)
    status: str = Field(...)
    defeitos: Optional[List[str]] = None
    obs: str = Field("", max_length=2500)
    
    @field_validator('os', mode="before")
    def os_must_be_numeric(cls, v):
        if isinstance(v, str) and not v.strip().isdigit():
            raise ValueError("O.S. deve conter apenas números")
        return v.strip() if isinstance(v, str) else v
    
    @field_validator('modelo', 'soldador', 'processo', 'status', mode="before")
    def max_100_chars(cls, v):
        if isinstance(v, str):
            v_str = v.strip()
            if len(v_str) > 100:
                raise ValueError(f"Campo excede 100 caracteres")
            return v_str
        return v
    
    @field_validator('obs', mode="before")
    def obs_max_2500(cls, v):
        if isinstance(v, str):
            v_str = v.strip()
            if len(v_str) > 2500:
                raise ValueError("Obs excede 2500 caracteres")
            return v_str
        return v

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
