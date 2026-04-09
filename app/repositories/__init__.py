from .base import BaseRepository
from .usuario import UsuarioRepository
from .inspecao import InspecaoRepository
from .soldador import SoldadorRepository
from .catalogo import CatalogoRepository
from .auditoria import AuditoriaRepository

# Helpers se houver injeção de dependência via funções prontas
def get_usuario_repo(db) -> UsuarioRepository:
    return UsuarioRepository(db)

def get_inspecao_repo(db) -> InspecaoRepository:
    return InspecaoRepository(db)

def get_soldador_repo(db) -> SoldadorRepository:
    return SoldadorRepository(db)

def get_catalogo_repo(db) -> CatalogoRepository:
    return CatalogoRepository(db)

__all__ = [
    "BaseRepository",
    "UsuarioRepository",
    "InspecaoRepository",
    "SoldadorRepository",
    "CatalogoRepository",
    "AuditoriaRepository",
    "get_usuario_repo",
    "get_inspecao_repo",
    "get_soldador_repo",
    "get_catalogo_repo"
]
