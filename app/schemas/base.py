from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class PaginationParams(BaseModel):
    page: int = Field(1, ge=1)
    per_page: int = Field(20, ge=1, le=100)

class AuditableBase(BaseModel):
    criado_em: Optional[datetime] = None
    
    class Config:
        from_attributes = True
