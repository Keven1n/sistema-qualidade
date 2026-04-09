import time
from typing import Dict, Any, Optional

class CacheManager:
    """
    ⚠️ ATENÇÃO: Cache simples em memória. 
    Use APENAS se rodar a aplicação com um único worker 
    (ex: Uvicorn puro, sem Gunicorn multi-workers). 
    Para cenários com múltiplos workers, substitua pelo Redis 
    para não sofrer com estados dessincronizados na UI.
    """
    
    def __init__(self, ttl_seconds: int = 600):  # Default 10 minutos
        self.cache: Dict[str, Any] = {}
        self.ttl = ttl_seconds
        
    def get(self, key: str) -> Optional[Any]:
        if key in self.cache:
            item = self.cache[key]
            if time.time() - item['timestamp'] < self.ttl:
                return item['data']
            else:
                del self.cache[key]
        return None
        
    def set(self, key: str, data: Any):
        self.cache[key] = {
            'data': data,
            'timestamp': time.time()
        }
        
    def invalidate(self, key: str):
        if key in self.cache:
            del self.cache[key]

# Instâncias globais (Singletons para o Worker)
soldadores_cache = CacheManager()
catalogo_cache = CacheManager()
