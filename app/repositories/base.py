from typing import TypeVar, Generic, Optional, List, Type
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models import Base

T = TypeVar('T', bound=Base)

class BaseRepository(Generic[T]):
    """Repositório genérico que elimina duplicação de CRUD e implementa UoW local."""
    
    def __init__(self, db: Session, model: Type[T]):
        self.db = db
        self.model = model
    
    def find_by_id(self, id: int) -> Optional[T]:
        return self.db.query(self.model).filter(self.model.id == id).first()
    
    def find_all(self, limit: int = None, offset: int = 0) -> List[T]:
        query = self.db.query(self.model)
        if limit:
            query = query.limit(limit).offset(offset)
        return query.all()
    
    def count(self, **filters) -> int:
        query = self.db.query(self.model)
        for key, value in filters.items():
            if hasattr(self.model, key) and value is not None:
                query = query.filter(getattr(self.model, key) == value)
        return query.count()
    
    def create(self, obj: T) -> T:
        self.db.add(obj)
        self.db.flush()  # Delegs commit to UoW / Service layer
        return obj
    
    def update(self, id: int, **kwargs) -> Optional[T]:
        obj = self.find_by_id(id)
        if not obj:
            return None
        for key, value in kwargs.items():
            if hasattr(obj, key):
                setattr(obj, key, value)
        self.db.flush()
        return obj
    
    def delete(self, id: int) -> bool:
        obj = self.find_by_id(id)
        if not obj:
            return False
        self.db.delete(obj)
        self.db.flush()
        return True
    
    def toggle_boolean_field(self, id: int, field_name: str) -> Optional[T]:
        """Toggle qualquer campo booleano (ativo, etc)"""
        obj = self.find_by_id(id)
        if not obj or not hasattr(obj, field_name):
            return None
        current_value = getattr(obj, field_name)
        setattr(obj, field_name, not current_value)
        self.db.flush()
        return obj
    
    def paginate(self, page: int = 1, per_page: int = 20, **filters):
        """Retorna (items, total, pages)"""
        query = self.db.query(self.model)
        
        # Aplicar filtros
        for key, value in filters.items():
            if hasattr(self.model, key) and value is not None:
                query = query.filter(getattr(self.model, key) == value)
        
        total = query.count()
        total_pages = max(1, (total - 1) // per_page + 1)
        page = max(1, min(page, total_pages))
        
        items = query.offset((page - 1) * per_page).limit(per_page).all()
        
        return {
            "items": items,
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages
        }
