from sqlalchemy.orm import Session
from app.models import Usuario, TentativaLogin
from app.repositories.usuario import UsuarioRepository
from app.exceptions import AccountLockedError, PermissionDenied, DuplicateResourceError
from app.services.base import BaseCrudService
from app.services.auditoria import registrar_auditoria
import bcrypt

class UsuarioService(BaseCrudService[Usuario, UsuarioRepository]):
    def __init__(self, db: Session):
        super().__init__(UsuarioRepository(db), resource_name="Usuário")
        self.db = db
        
    def criar_novo_usuario(self, usuario_data: dict, admin_logado_id: str) -> Usuario:
        if self.repo.username_exists(usuario_data['usuario']):
            raise DuplicateResourceError(f"Usuário {usuario_data['usuario']}")
            
        hash_senha = bcrypt.hashpw(usuario_data['senha'].encode(), bcrypt.gensalt()).decode()
        
        user = self.repo.create_user(
            usuario=usuario_data['usuario'],
            nome=usuario_data['nome'],
            hash_senha=hash_senha,
            papel=usuario_data['papel']
        )
        
        registrar_auditoria(self.db, admin_logado_id, "usuario_criado", alvo=user.usuario)
        
        self.db.commit()
        self.db.refresh(user)
        return user
        
    def alterar_papel(self, usuario_id: int, novo_papel: str, admin_logado_id: str) -> Usuario:
        usuario = self.get_by_id(usuario_id)
        if usuario.usuario == "kevin":  # Hardcode proteção do admin principal
            raise PermissionDenied("Não é possível alterar o papel do superadmin")
            
        usuario.papel = novo_papel
        registrar_auditoria(self.db, admin_logado_id, "papel_alterado", alvo=usuario.usuario, detalhe=novo_papel)
        
        self.db.commit()
        self.db.refresh(usuario)
        return usuario

class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = UsuarioRepository(db)
        
    def autenticar(self, username: str, senha_plana: str) -> bool:
        self._verificar_bloqueio(username)
        
        user = self.repo.find_by_username_active(username)
        if not user:
            self._registrar_tentativa_falha(username)
            return False
            
        is_valid = bcrypt.checkpw(senha_plana.encode(), user.hash_senha.encode())
        if is_valid:
            self._registrar_tentativa_sucesso(username)
            registrar_auditoria(self.db, username, "login_realizado")
            self.db.commit()
            return True
        else:
            self._registrar_tentativa_falha(username)
            return False
            
    def _verificar_bloqueio(self, username: str):
        # A lógica de bloqueio de muitas falhas será importada e adaptada aqui.
        pass
        
    def _registrar_tentativa_falha(self, username: str):
        pass
        
    def _registrar_tentativa_sucesso(self, username: str):
        pass
