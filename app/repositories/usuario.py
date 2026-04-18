from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.models import Usuario
from app.repositories.base import BaseRepository
from typing import Optional

class UsuarioRepository(BaseRepository[Usuario]):
    def __init__(self, db: Session):
        super().__init__(db, Usuario)
    
    def find_by_username(self, usuario: str) -> Optional[Usuario]:
        usuario = usuario.strip().lower()
        return self.db.query(Usuario).filter(Usuario.usuario == usuario).first()
    
    def find_by_username_active(self, usuario: str) -> Optional[Usuario]:
        usuario = usuario.strip().lower()
        return self.db.query(Usuario).filter(
            and_(Usuario.usuario == usuario, Usuario.ativo == True)
        ).first()
    
    def username_exists(self, usuario: str) -> bool:
        return self.find_by_username(usuario) is not None
    
    def create_user(self, usuario: str, nome: str, hash_senha: str, papel: str = "inspetor") -> Usuario:
        user = Usuario(
            usuario=usuario.strip().lower(),
            nome=nome.strip(),
            hash_senha=hash_senha,
            papel=papel
        )
        return self.create(user)
