from sqlalchemy.orm import Session
from app.models import Auditoria
from app.repositories.base import BaseRepository

class AuditoriaRepository(BaseRepository[Auditoria]):
    def __init__(self, db: Session):
        super().__init__(db, Auditoria)
    
    def get_recent(self, limit: int = 50):
        return self.db.query(Auditoria).order_by(Auditoria.momento.desc()).limit(limit).all()
