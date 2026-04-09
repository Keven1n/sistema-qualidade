from sqlalchemy.orm import Session
from app.models import Soldador
from app.repositories.soldador import SoldadorRepository
from app.services.base import BaseCrudService
from app.services.cache import soldadores_cache
from app.services.auditoria import registrar_auditoria
from app.exceptions import DuplicateResourceError

class SoldadorService(BaseCrudService[Soldador, SoldadorRepository]):
    def __init__(self, db: Session):
        super().__init__(SoldadorRepository(db), resource_name="Soldador")
        self.db = db
        
    def criar_soldador(self, soldador_data: dict, usuario_logado_id: str) -> Soldador:
        if self.repo.nome_exists(soldador_data['nome']):
            raise DuplicateResourceError(f"Soldador '{soldador_data['nome']}'")
            
        novo = Soldador(nome=soldador_data['nome'])
        soldador = self.repo.create(novo)
        
        registrar_auditoria(self.db, usuario_logado_id, "soldador_criado", alvo=novo.nome)
        
        self.db.commit()
        self.db.refresh(soldador)
        soldadores_cache.invalidate("dropdown") # Invalida o cache afetado
        return soldador

    def toggle(self, id: int, field_name: str = "ativo") -> Soldador:
        obj = super().toggle(id, field_name)
        soldadores_cache.invalidate("dropdown")
        return obj
