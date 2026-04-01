# app/models.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.database import Base

class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    usuario = Column(String, unique=True, index=True, nullable=False)
    nome = Column(String, nullable=False)
    hash_senha = Column(String, nullable=False)
    ativo = Column(Boolean, default=True)
    papel = Column(String, default="inspetor")
    criado_em = Column(DateTime(timezone=True), server_default=func.now())

class Inspecao(Base):
    __tablename__ = "inspecoes"

    id = Column(Integer, primary_key=True, index=True)
    data = Column(String, index=True)
    os = Column(String, index=True)
    modelo = Column(String)
    soldador = Column(String)
    processo = Column(String)
    status = Column(String)
    defeitos = Column(String)
    obs = Column(String)
    fotos = Column(String)
    assinatura = Column(String)
    reinspeção_de = Column(Integer, ForeignKey("inspecoes.id"), nullable=True)

class Soldador(Base):
    __tablename__ = "soldadores"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, unique=True, nullable=False)
    ativo = Column(Boolean, default=True)

class Catalogo(Base):
    __tablename__ = "catalogo"

    id = Column(Integer, primary_key=True, index=True)
    linha = Column(String, nullable=False)
    modelo = Column(String, nullable=False)
    ativo = Column(Boolean, default=True)

class Auditoria(Base):
    __tablename__ = "auditoria"

    id = Column(Integer, primary_key=True, index=True)
    momento = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    usuario = Column(String, index=True, nullable=False)
    acao = Column(String, nullable=False)
    alvo = Column(String)
    detalhe = Column(String)

class TentativaLogin(Base):
    __tablename__ = "tentativas_login"

    id = Column(Integer, primary_key=True, index=True)
    usuario = Column(String, index=True, nullable=False)
    momento = Column(String, nullable=False)
    sucesso = Column(Integer, default=0)