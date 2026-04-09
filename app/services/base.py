from typing import TypeVar, Generic, List, Optional
from app.repositories.base import BaseRepository
from app.exceptions import NotFoundError
from app.models import Base

T = TypeVar('T', bound=Base)
R = TypeVar('R', bound=BaseRepository)

class BaseCrudService(Generic[T, R]):
    """Implementa Unit of Work para o repositório genérico"""
    def __init__(self, repo: R, resource_name: str = "Recurso"):
        self.repo = repo
        self.resource_name = resource_name
        
    def get_by_id(self, id: int) -> T:
        obj = self.repo.find_by_id(id)
        if not obj:
            raise NotFoundError(self.resource_name)
        return obj
        
    def list_all(self, limit: int = None, offset: int = 0) -> List[T]:
        return self.repo.find_all(limit, offset)
        
    def create(self, obj: T) -> T:
        created_obj = self.repo.create(obj)
        self.repo.db.commit()
        self.repo.db.refresh(created_obj)
        return created_obj
        
    def update(self, id: int, **kwargs) -> T:
        obj = self.repo.update(id, **kwargs)
        if not obj:
            raise NotFoundError(self.resource_name)
        self.repo.db.commit()
        self.repo.db.refresh(obj)
        return obj
        
    def delete(self, id: int) -> bool:
        success = self.repo.delete(id)
        if not success:
            raise NotFoundError(self.resource_name)
        self.repo.db.commit()
        return success
        
    def toggle(self, id: int, field_name: str = "ativo") -> T:
        obj = self.repo.toggle_boolean_field(id, field_name)
        if not obj:
            raise NotFoundError(self.resource_name)
        self.repo.db.commit()
        self.repo.db.refresh(obj)
        return obj
        
    def paginate(self, page: int = 1, per_page: int = 20, **filters):
        return self.repo.paginate(page, per_page, **filters)
