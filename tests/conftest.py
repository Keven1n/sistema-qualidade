# tests/conftest.py
import pytest
import bcrypt
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import get_db_session, Base
from app.models import Usuario

# Cria um banco de dados SQLite temporário na memória RAM
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session", autouse=True)
def setup_db():
    # Cria as tabelas antes de todos os testes
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    
    # Injeta um usuário admin falso para usarmos nos testes
    h = bcrypt.hashpw(b"senha123", bcrypt.gensalt()).decode()
    teste_user = Usuario(usuario="admin_teste", nome="Admin Teste", hash_senha=h, papel="admin")
    db.add(teste_user)
    db.commit()
    db.close()
    
    yield
    # Apaga tudo no final
    Base.metadata.drop_all(bind=engine)

@pytest.fixture()
def client():
    # Esta função substitui o banco do Postgres pelo nosso banco em memória
    def override_get_db():
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()
            
    app.dependency_overrides[get_db_session] = override_get_db
    yield TestClient(app)