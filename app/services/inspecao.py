from sqlalchemy.orm import Session
from app.models import Inspecao
from app.repositories.inspecao import InspecaoRepository
from app.services.base import BaseCrudService
from app.services.auditoria import registrar_auditoria

class InspecaoService(BaseCrudService[Inspecao, InspecaoRepository]):
    def __init__(self, db: Session):
        super().__init__(InspecaoRepository(db), resource_name="Inspeção")
        self.db = db
        
    def criar_inspecao(self, inspecao_data: dict, usuario_logado: str) -> Inspecao:
        # Aqui ficará as validações pesadas como assinaturas em B64 
        # que antes poluíam a rota
        
        nova = Inspecao(**inspecao_data)
        insp_criada = self.repo.create(nova)
        
        registrar_auditoria(
            self.db,
            usuario_logado, 
            "inspecao_criada", 
            alvo=insp_criada.os
        )
        
        self.db.commit()
        self.db.refresh(insp_criada)
        return insp_criada
