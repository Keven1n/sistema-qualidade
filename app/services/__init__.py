from .usuario import UsuarioService, AuthService
from .inspecao import InspecaoService
from .soldador import SoldadorService
from .catalogo import CatalogoService
from .auditoria import AuditoriaService, registrar_auditoria

def get_usuario_service(db) -> UsuarioService:
    return UsuarioService(db)

def get_auth_service(db) -> AuthService:
    return AuthService(db)

def get_inspecao_service(db) -> InspecaoService:
    return InspecaoService(db)

def get_soldador_service(db) -> SoldadorService:
    return SoldadorService(db)

def get_catalogo_service(db) -> CatalogoService:
    return CatalogoService(db)

__all__ = [
    "UsuarioService", "AuthService", "InspecaoService",
    "SoldadorService", "CatalogoService", "AuditoriaService",
    "registrar_auditoria",
    "get_usuario_service", "get_auth_service", "get_inspecao_service",
    "get_soldador_service", "get_catalogo_service"
]
