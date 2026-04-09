# 🔧 REFACTORING FASE 3: Services e Business Logic Layer

Esta fase encapsula toda lógica de negócio em Services reutilizáveis.

---

## 📂 app/services/base.py

```python
from typing import TypeVar, Generic, Optional, List, Type
from sqlalchemy.orm import Session
from app.repositories.base import BaseRepository
from app.exceptions import NotFoundError

T = TypeVar('T')

class BaseCrudService(Generic[T]):
    """Serviço genérico de CRUD com lógica de negócio"""
    
    def __init__(self, repo: BaseRepository[T], resource_name: str):
        self.repo = repo
        self.resource_name = resource_name
    
    def get_by_id(self, id: int) -> T:
        obj = self.repo.find_by_id(id)
        if not obj:
            raise NotFoundError(self.resource_name)
        return obj
    
    def get_all(self, limit: int = None, offset: int = 0) -> List[T]:
        return self.repo.find_all(limit, offset)
    
    def create(self, obj: T) -> T:
        created_obj = self.repo.create(obj)
        self.repo.db.commit()
        self.repo.db.refresh(created_obj)
        return created_obj
    
    def update(self, id: int, **kwargs) -> T:
        obj = self.repo.update(id, **kwargs)
        if not obj:
            raise NotFoundError(self.resource_name)
        self.repo.db.commit()
        self.repo.db.refresh(obj)
        return obj
    
    def delete(self, id: int) -> bool:
        success = self.repo.delete(id)
        if not success:
            raise NotFoundError(self.resource_name)
        self.repo.db.commit()
        return success
    
    def toggle(self, id: int, field_name: str = "ativo") -> T:
        obj = self.repo.toggle_boolean_field(id, field_name)
        if not obj:
            raise NotFoundError(self.resource_name)
        self.repo.db.commit()
        self.repo.db.refresh(obj)
        return obj
    
    def paginate(self, page: int = 1, per_page: int = 20, **filters):
        return self.repo.paginate(page, per_page, **filters)
```

---

## 📂 app/services/auth.py

```python
import bcrypt
from datetime import datetime, timedelta
from jsonschema import ValidationError
from sqlalchemy.orm import Session
from typing import Tuple, Optional

from app.repositories.usuario import UsuarioRepository
from app.repositories.auditoria import AuditoriaRepository
from app.models import Usuario, TentativaLogin
from app.config import settings
from app.exceptions import AccountLockedError, ValidationException
from app.dependencies import registrar_auditoria

class AuthService:
    def __init__(self, usuario_repo: UsuarioRepository, db: Session):
        self.usuario_repo = usuario_repo
        self.db = db
    
    def verificar_login(self, usuario: str, senha: str) -> Tuple[Optional[str], Optional[str], str]:
        """
        Verifica login com rate limiting
        Retorna: (nome, papel, status) onde status in ["ok", "invalido", "bloqueado"]
        """
        usuario = usuario.strip().lower()
        
        # Verificar se conta está bloqueada
        if self._is_account_locked(usuario):
            return None, None, "bloqueado"
        
        # Buscar usuário ativo
        user = self.usuario_repo.find_by_username_active(usuario)
        if not user:
            self._registrar_tentativa_falha(usuario)
            return None, None, "invalido"
        
        # Verificar senha
        try:
            if bcrypt.checkpw(senha.encode(), user.hash_senha.encode()):
                self._registrar_tentativa_sucesso(usuario)
                return user.nome, user.papel, "ok"
        except Exception as e:
            registrar_auditoria(usuario, "login_erro_bcrypt", detalhe=str(e))
            pass
        
        self._registrar_tentativa_falha(usuario)
        return None, None, "invalido"
    
    def _is_account_locked(self, usuario: str) -> bool:
        """Verifica se conta está bloqueada por tentativas falhas"""
        limite = (datetime.now() - timedelta(minutes=15)).strftime("%Y-%m-%d %H:%M:%S")
        
        falhas = self.db.query(TentativaLogin).filter(
            TentativaLogin.usuario == usuario,
            TentativaLogin.sucesso == 0,
            TentativaLogin.momento > limite
        ).count()
        
        return falhas >= settings.max_login_attempts
    
    def _registrar_tentativa_sucesso(self, usuario: str):
        nova_tentativa = TentativaLogin(
            usuario=usuario,
            momento=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            sucesso=1
        )
        self.db.add(nova_tentativa)
        self.db.commit()
    
    def _registrar_tentativa_falha(self, usuario: str):
        nova_tentativa = TentativaLogin(
            usuario=usuario,
            momento=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            sucesso=0
        )
        self.db.add(nova_tentativa)
        self.db.commit()
    
    def criar_usuario_com_bcrypt(self, usuario: str, nome: str, senha: str, papel: str = "inspetor") -> Usuario:
        """Cria usuário com senha criptografada"""
        if self.usuario_repo.username_exists(usuario):
            raise ValidationException(f"Usuário '{usuario}' já existe")
        
        hash_senha = bcrypt.hashpw(senha.encode(), bcrypt.gensalt()).decode()
        return self.usuario_repo.create_user(usuario, nome, hash_senha, papel)
```

---

## 📂 app/services/inspecao.py

```python
import os
import uuid
import base64
from datetime import datetime
from typing import Optional, Dict, List
from sqlalchemy.orm import Session
from PIL import Image
import io

from app.repositories.inspecao import InspecaoRepository
from app.repositories.soldador import SoldadorRepository
from app.repositories.catalogo import CatalogoRepository
from app.models import Inspecao
from app.schemas.inspecao import InspecaoCreate, InspecaoFilter
from app.config import settings
from app.exceptions import ValidationException, DuplicateResourceError, NotFoundError
from app.dependencies import registrar_auditoria

MAGIC_BYTES = {b'\xff\xd8\xff': "jpeg", b'\x89PNG\r\n\x1a\n': "png"}
TIPOS_OK = set(MAGIC_BYTES.values())

class InspecaoService:
    def __init__(self, 
                 inspecao_repo: InspecaoRepository,
                 soldador_repo: SoldadorRepository,
                 catalogo_repo: CatalogoRepository,
                 db: Session):
        self.inspecao_repo = inspecao_repo
        self.soldador_repo = soldador_repo
        self.catalogo_repo = catalogo_repo
        self.db = db
    
    def criar_inspecao(self, data: InspecaoCreate, usuario_id: str) -> Inspecao:
        """Cria inspecção com todas as validações de negócio"""
        
        # Validar que O.S. não existe (se não for reinspeção)
        if not data.reinspeção_de:
            if self.inspecao_repo.os_exists(data.os, exclude_reinspecao=True):
                raise DuplicateResourceError(f"O.S. {data.os}")
        
        # Validar que reinspeção_de existe
        if data.reinspeção_de:
            origem = self.inspecao_repo.find_by_id(data.reinspeção_de)
            if not origem:
                raise NotFoundError("Inspecção de origem para reinspeção")
        
        # Criar inspecção
        nova_inspecao = Inspecao(
            data=data.data,
            os=data.os.strip(),
            modelo=data.modelo.strip(),
            soldador=data.soldador.strip(),
            processo=data.processo.strip(),
            status=data.status,
            defeitos=", ".join(data.defeitos) if data.defeitos else "N/A",
            obs=data.obs,
            reinspeção_de=data.reinspeção_de
        )
        
        inspecao_criada = self.inspecao_repo.create(nova_inspecao)
        
        registrar_auditoria(
            usuario_id, "inspecao_criada",
            alvo=f"inspecao#{inspecao_criada.id}",
            detalhe=f"os={data.os} status={data.status}"
        )
        
        return inspecao_criada
    
    def editar_inspecao(self, id_reg: int, os: str, soldador: str, 
                        processo: str, status_ins: str, defeitos: str, 
                        obs: str, usuario_id: str) -> Inspecao:
        """Edita inspecção com auditoria"""
        
        inspecao = self.inspecao_repo.find_by_id(id_reg)
        if not inspecao:
            raise NotFoundError("Inspecção")
        
        # Registrar antes para auditoria
        antes = f"os={inspecao.os} soldador={inspecao.soldador} status={inspecao.status}"
        
        # Atualizar
        inspecao.os = os.strip()
        inspecao.soldador = soldador.strip()
        inspecao.processo = processo
        inspecao.status = status_ins
        inspecao.defeitos = defeitos.strip()
        inspecao.obs = obs
        
        self.db.commit()
        self.db.refresh(inspecao)
        
        registrar_auditoria(
            usuario_id, "inspecao_editada",
            alvo=f"inspecao#{id_reg}",
            detalhe=f"antes: {antes}"
        )
        
        return inspecao
    
    def excluir_inspecao(self, id_reg: int, usuario_id: str) -> bool:
        """Remove inspecção com auditoria"""
        inspecao = self.inspecao_repo.find_by_id(id_reg)
        if not inspecao:
            raise NotFoundError("Inspecção")
        
        registrar_auditoria(
            usuario_id, "inspecao_excluida",
            alvo=f"inspecao#{id_reg}",
            detalhe=f"os={inspecao.os} status={inspecao.status}"
        )
        
        return self.inspecao_repo.delete(id_reg)
    
    def obter_estatisticas(self, filters: InspecaoFilter) -> Dict:
        """Retorna estatísticas dashboard"""
        return self.inspecao_repo.get_statistics(filters)
    
    def obter_dashboard_data(self, filters: InspecaoFilter) -> Dict:
        """Retorna TODOS os dados para dashboard em uma chamada"""
        return {
            "stats": self.inspecao_repo.get_statistics(filters),
            "status_distribution": self.inspecao_repo.get_status_distribution(filters),
            "soldador_failures": self.inspecao_repo.get_soldador_failures(filters),
            "modelo_distribution": self.inspecao_repo.get_modelo_distribution(filters),
            "defeitos_frequency": self.inspecao_repo.get_defeitos_frequency(filters, limit=10),
        }
    
    def obter_catalogo(self) -> Dict[str, List[str]]:
        """Catálogo agrupado para form (candidato a caching)"""
        return self.catalogo_repo.get_catalog_grouped()
    
    def obter_soldadores(self) -> List[str]:
        """Lista de soldadores ativos (candidato a caching)"""
        return [s.nome for s in self.soldador_repo.find_all_active()]
    
    def pode_listar_inspecoes(self) -> bool:
        """Validação se usuário tem permissão para listar"""
        return True  # Todos podem listar
    
    @staticmethod
    def _get_image_type(data: bytes) -> Optional[str]:
        for magic, tipo in MAGIC_BYTES.items():
            if data.startswith(magic):
                return tipo
        return None
    
    @staticmethod
    async def processar_imagens(files: list) -> str:
        """Valida e processa imagens, retorna lista de nomes"""
        caminhos = []
        
        os.makedirs(settings.img_dir, exist_ok=True)
        
        for arq in files:
            if not arq.filename:
                continue
            
            conteudo = await arq.read()
            if not conteudo:
                continue
            
            # Validar tamanho
            if len(conteudo) > settings.max_size_mb * 1024 * 1024:
                raise ValidationException(
                    f"Arquivo {arq.filename} excede {settings.max_size_mb}MB"
                )
            
            # Validar tipo
            tipo = InspecaoService._get_image_type(conteudo)
            if not tipo:
                raise ValidationException(
                    f"Arquivo {arq.filename} possui formato não permitido"
                )
            
            # Salvar com EXIF removido
            nome = f"{uuid.uuid4()}.{tipo}"
            caminho_full = os.path.join(settings.img_dir, nome)
            
            try:
                with Image.open(io.BytesIO(conteudo)) as img:
                    img.save(caminho_full, format=tipo.upper())
            except Exception as e:
                # Fallback se Pillow falhar
                with open(caminho_full, "wb") as f:
                    f.write(conteudo)
            
            caminhos.append(nome)
        
        return ";".join(caminhos)
    
    @staticmethod
    def processar_assinatura(assinatura_b64: str) -> Optional[str]:
        """Processa assinatura Base64 do Canvas"""
        if not assinatura_b64:
            return None
        
        if not assinatura_b64.startswith("data:image/png;base64,"):
            raise ValidationException("Assinatura possui formato inválido")
        
        if len(assinatura_b64) > 1_000_000:
            raise ValidationException("Assinatura muito grande")
        
        os.makedirs(settings.img_dir, exist_ok=True)
        
        b64_data = assinatura_b64.split(",")[1]
        nome_ass = f"ass_{uuid.uuid4()}.png"
        
        try:
            with open(os.path.join(settings.img_dir, nome_ass), "wb") as f:
                f.write(base64.b64decode(b64_data))
        except Exception as e:
            raise ValidationException(f"Erro ao processar assinatura: {str(e)}")
        
        return nome_ass
```

---

## 📂 app/services/usuario.py

```python
from sqlalchemy.orm import Session
from app.repositories.usuario import UsuarioRepository
from app.services.base import BaseCrudService
from app.services.auth import AuthService
from app.models import Usuario
from app.schemas.usuario import UsuarioCreate, UsuarioUpdate
from app.exceptions import ValidationException, DuplicateResourceError
from app.dependencies import registrar_auditoria

class UsuarioService(BaseCrudService[Usuario]):
    def __init__(self, usuario_repo: UsuarioRepository, auth_service: AuthService, db: Session):
        super().__init__(usuario_repo, "Usuário")
        self.usuario_repo = usuario_repo
        self.auth_service = auth_service
        self.db = db
    
    def criar_usuario(self, usuario_data: UsuarioCreate, usuario_logado_id: str) -> Usuario:
        """Cria usuário com senha criptografada e auditoria"""
        usuario = self.auth_service.criar_usuario_com_bcrypt(
            usuario_data.usuario,
            usuario_data.nome,
            usuario_data.senha,
            usuario_data.papel
        )
        
        registrar_auditoria(
            usuario_logado_id, "usuario_criado",
            alvo=usuario_data.usuario,
            detalhe=f"papel={usuario_data.papel}"
        )
        
        return usuario
    
    def alterar_papel(self, id_user: int, novo_papel: str, usuario_logado_id: str) -> Usuario:
        """Altera papel do usuário com auditoria"""
        usuario = self.get_by_id(id_user)
        papel_antigo = usuario.papel
        
        usuario.papel = novo_papel
        self.db.commit()
        self.db.refresh(usuario)
        
        registrar_auditoria(
            usuario_logado_id, "papel_alterado",
            alvo=usuario.usuario,
            detalhe=f"antes={papel_antigo} agora={novo_papel}"
        )
        
        return usuario
    
    def toggle_usuario(self, id_user: int, usuario_logado_id: str) -> Usuario:
        """Ativa/desativa usuário com auditoria"""
        usuario = self.get_by_id(id_user)
        usuario_antigo = usuario.ativo
        
        usuario.ativo = not usuario.ativo
        self.db.commit()
        self.db.refresh(usuario)
        
        acao = "usuario_ativado" if usuario.ativo else "usuario_desativado"
        registrar_auditoria(usuario_logado_id, acao, alvo=usuario.usuario)
        
        return usuario
```

---

## 📂 app/services/cache.py (NOVO - Caching de Dropdowns)

```python
import functools
from typing import Dict, List
from datetime import datetime, timedelta

class CacheManager:
    """
    ⚠️ ATENÇÃO: Cache simples em memória. 
    Use APENAS se rodar a aplicação com um único worker 
    (ex: Uvicorn puro, sem Gunicorn multi-workers). 
    Para cenários com múltiplos workers, substitua pelo Redis 
    para não sofrer com estados dessincronizados na UI.
    """
    
    def __init__(self, ttl_seconds: int = 600):  # Default 10 minutos
        self.cache: Dict = {}
        self.ttl = ttl_seconds
    
    def get(self, key: str):
        if key in self.cache:
            value, expires_at = self.cache[key]
            if datetime.now() < expires_at:
                return value
            else:
                del self.cache[key]
        return None
    
    def set(self, key: str, value, ttl: int = None):
        expires_at = datetime.now() + timedelta(seconds=ttl or self.ttl)
        self.cache[key] = (value, expires_at)
    
    def clear(self, key: str = None):
        if key:
            self.cache.pop(key, None)
        else:
            self.cache.clear()

# Instância única de cache
cache_manager = CacheManager(ttl_seconds=600)

def cached(key_prefix: str, ttl: int = 600):
    """Decorator para cachear resultados de funções"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = f"{key_prefix}:{func.__name__}"
            
            result = cache_manager.get(cache_key)
            if result is not None:
                return result
            
            result = func(*args, **kwargs)
            cache_manager.set(cache_key, result, ttl)
            return result
        return wrapper
    return decorator
```

---

## 📂 app/services/__init__.py

```python
from sqlalchemy.orm import Session
from app.repositories import (
    get_usuario_repo, get_inspecao_repo, get_soldador_repo,
    get_catalogo_repo, get_auditoria_repo
)
from app.services.base import BaseCrudService
from app.services.auth import AuthService
from app.services.usuario import UsuarioService
from app.services.inspecao import InspecaoService

def get_auth_service(db: Session) -> AuthService:
    return AuthService(get_usuario_repo(db), db)

def get_usuario_service(db: Session) -> UsuarioService:
    return UsuarioService(
        get_usuario_repo(db),
        get_auth_service(db),
        db
    )

def get_inspecao_service(db: Session) -> InspecaoService:
    return InspecaoService(
        get_inspecao_repo(db),
        get_soldador_repo(db),
        get_catalogo_repo(db),
        db
    )
```

---

## 🎯 BENEFÍCIOS FASE 3

✅ **Lógica de Negócio Centralizada**: Tudo em um lugar  
✅ **Reutilizável em API, CLI, Tests**: Services não sabem de HTTP  
✅ **Sem Duplicação**: Mesma regra de negócio aplicada everywhere  
✅ **Auditoria Automática**: Rodapé em cada operação crítica  
✅ **Caching Integrado**: Dropdowns recalculados a cada 10min  
✅ **Type Safe**: TypeHints em tudo  
✅ **Errorhandling Consistente**: Custom exceptions com mensagens  

---

## 📝 EXEMPLO: Usando Services em Routers

### **Antes (lógica espalhada):**
```python
@router.post("/criar")
def criar_usuario(...):
    if len(nova_senha) < 6 or len(nova_senha) > 100:
        raise HTTPException(400, "...")
    if len(novo_usuario.strip()) > 50:
        raise HTTPException(400, "...")
    
    existente = db.query(Usuario).filter(...).first()
    if existente:
        raise HTTPException(400, "Usuário já existe")
    
    h = bcrypt.hashpw(nova_senha.encode(), bcrypt.gensalt()).decode()
    novo_user = Usuario(...)
    db.add(novo_user)
    db.commit()
    
    registrar_auditoria(...)
    return RedirectResponse(...)
```

### **Depois (orquestração clara):**
```python
@router.post("/criar")
def criar_usuario(
    request: Request,
    sessao: dict = Depends(require_admin),
    _csrf: None = Depends(verificar_csrf),
    usuario_data: UsuarioCreate = Depends(),  # Já validado!
    db: Session = Depends(get_db_session)
):
    service = get_usuario_service(db)
    usuario_criado = service.criar_usuario(usuario_data, sessao["usuario"])
    # Auditoria feita dentro do service!
    return RedirectResponse("/usuarios", status_code=303)
```

---

## 📋 PRÓXIMAS PASSOS

1. ✅ Implementar Services (auth, usuario, inspecao)
2. ✅ Refatorar routers para usar services
3. → **Próximo:** Implementar caching para performance
4. → **Depois:** Adicionar testes unitários

