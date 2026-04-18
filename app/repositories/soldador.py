from sqlalchemy.orm import Session
from app.models import Soldador
from app.repositories.base import BaseRepository

class SoldadorRepository(BaseRepository[Soldador]):
    def __init__(self, db: Session):
        super().__init__(db, Soldador)
        
    def nome_exists(self, nome: str) -> bool:
        return self.db.query(Soldador).filter(Soldador.nome == nome).first() is not None
