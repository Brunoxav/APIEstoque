"""
Banco de dados da API de Controle de Estoque.

Aqui ficam:
- conexão com o SQLite
- definição das tabelas de produtos e movimentações
- enums usados na lógica (tipo de movimentação)
"""

from datetime import datetime
from pathlib import Path
from enum import Enum

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    DateTime,
    Text,
    ForeignKey,
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship


# -----------------------------------------------------------------------------
# Caminho do banco
# O arquivo .db fica sempre na pasta do projeto.
# -----------------------------------------------------------------------------
PASTA_DO_PROJETO = Path(__file__).resolve().parent
ARQUIVO_DO_BANCO = PASTA_DO_PROJETO / "estoque.db"
URL_DO_BANCO = "sqlite:///" + str(ARQUIVO_DO_BANCO).replace("\\", "/")

# SQLite no FastAPI precisa desse flag para permitir uso em mais de uma thread.
engine = create_engine(URL_DO_BANCO, connect_args={"check_same_thread": False})
SessaoLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# -----------------------------------------------------------------------------
# Enums: tipo de movimentação
# -----------------------------------------------------------------------------
class TipoMovimentacao(str, Enum):
    """Tipo da movimentação de estoque."""

    ENTRADA = "entrada"
    SAIDA = "saida"


# -----------------------------------------------------------------------------
# Modelo da tabela "produtos"
# -----------------------------------------------------------------------------
class Produto(Base):
    __tablename__ = "produtos"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(200), nullable=False)
    sku = Column(String(50), nullable=True, unique=True)
    descricao = Column(Text, nullable=True)
    estoque_atual = Column(Integer, default=0, nullable=False)
    estoque_minimo = Column(Integer, default=0, nullable=False)
    criado_em = Column(DateTime, default=datetime.utcnow)
    atualizado_em = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    movimentacoes = relationship(
        "Movimentacao",
        back_populates="produto",
        cascade="all, delete-orphan",
    )


# -----------------------------------------------------------------------------
# Modelo da tabela "movimentacoes"
# -----------------------------------------------------------------------------
class Movimentacao(Base):
    __tablename__ = "movimentacoes"

    id = Column(Integer, primary_key=True, index=True)
    produto_id = Column(Integer, ForeignKey("produtos.id"), nullable=False, index=True)
    tipo = Column(String(10), nullable=False)  # entrada | saida
    quantidade = Column(Integer, nullable=False)
    observacao = Column(Text, nullable=True)
    criado_em = Column(DateTime, default=datetime.utcnow)

    produto = relationship("Produto", back_populates="movimentacoes")


def criar_tabelas_se_nao_existirem() -> None:
    """Cria as tabelas no SQLite se ainda não existirem."""
    Base.metadata.create_all(bind=engine)


def obter_sessao():
    """
    Entrega uma sessão do banco para cada requisição.
    Usado pelo FastAPI via Depends.
    """
    sessao = SessaoLocal()
    try:
        yield sessao
    finally:
        sessao.close()

