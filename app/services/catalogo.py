from sqlalchemy.orm import Session
from app.models import Catalogo
from app.repositories.catalogo import CatalogoRepository
from app.services.base import BaseCrudService
from app.services.cache import catalogo_cache

class CatalogoService(BaseCrudService[Catalogo, CatalogoRepository]):
    def __init__(self, db: Session):
        super().__init__(CatalogoRepository(db), resource_name="Catálogo")
        self.db = db
        
    def create(self, obj: Catalogo) -> Catalogo:
        created = super().create(obj)
        catalogo_cache.invalidate("dropdown")
        return created
        
    def toggle(self, id: int, field_name: str = "ativo") -> Catalogo:
        obj = super().toggle(id, field_name)
        catalogo_cache.invalidate("dropdown")
        return obj
