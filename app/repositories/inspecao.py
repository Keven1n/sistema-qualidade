from sqlalchemy.orm import Session
from sqlalchemy import func, case
from app.models import Inspecao
from app.repositories.base import BaseRepository
from typing import Dict, Any

class InspecaoRepository(BaseRepository[Inspecao]):
    def __init__(self, db: Session):
        super().__init__(db, Inspecao)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Substitui N queries brutas por uma única agregação SQL"""
        result = self.db.query(
            func.count(Inspecao.id).label('total'),
            func.sum(case((Inspecao.status == 'Aprovado', 1), else_=0)).label('aprovados'),
            func.sum(case((Inspecao.status == 'Reprovado', 1), else_=0)).label('reprovados')
        ).first()
        
        return {
            "total": result.total or 0,
            "aprovados": result.aprovados or 0,
            "reprovados": result.reprovados or 0
        }
