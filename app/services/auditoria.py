from app.repositories.auditoria import AuditoriaRepository
from app.models import Auditoria
from sqlalchemy.orm import Session

class AuditoriaService:
    def __init__(self, auditoria_repo: AuditoriaRepository):
        self.repo = auditoria_repo
        
    def registrar(self, usuario: str, acao: str, alvo: str = None, detalhe: str = None):
        """Registra log mas NÃO commita sozinho. 
        Delega para quem iniciou a transação (Unit of Work)."""
        auditoria = Auditoria(
            usuario=usuario,
            acao=acao,
            alvo=alvo,
            detalhe=detalhe
        )
        self.repo.create(auditoria)
        # Atenção: não tem commit aqui para manter na mesma transação (mesmo db.flush)

# Helper rápido
def registrar_auditoria(db: Session, usuario_logado_id: str, acao: str, alvo: str = None, detalhe: str = None):
    repo = AuditoriaRepository(db)
    service = AuditoriaService(repo)
    service.registrar(usuario_logado_id, acao, alvo, detalhe)
