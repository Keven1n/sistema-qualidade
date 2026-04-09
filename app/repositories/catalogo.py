from sqlalchemy.orm import Session
from app.models import Catalogo
from app.repositories.base import BaseRepository

class CatalogoRepository(BaseRepository[Catalogo]):
    def __init__(self, db: Session):
        super().__init__(db, Catalogo)
