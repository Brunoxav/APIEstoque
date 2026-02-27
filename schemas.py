"""
Contratos de entrada e saída da API de Estoque (schemas).

Os schemas definem o formato dos dados: o que o cliente pode enviar
e o que a API devolve para produtos, movimentações e relatórios.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, conint

from database import TipoMovimentacao


# -----------------------------------------------------------------------------
# Produtos
# -----------------------------------------------------------------------------
class ProdutoCriar(BaseModel):
    """Dados necessários para cadastrar um novo produto."""

    nome: str = Field(..., min_length=1, max_length=200, description="Nome do produto")
    sku: Optional[str] = Field(
        default=None, max_length=50, description="Código interno/SKU (opcional)"
    )
    descricao: Optional[str] = Field(
        default=None, description="Descrição resumida do produto"
    )
    estoque_inicial: conint(ge=0) = Field(
        default=0, description="Quantidade inicial em estoque (opcional)"
    )
    estoque_minimo: conint(ge=0) = Field(
        default=0, description="Quantidade mínima desejada para alerta"
    )


class ProdutoAtualizar(BaseModel):
    """Atualização parcial de produto (apenas campos enviados)."""

    nome: Optional[str] = Field(None, min_length=1, max_length=200)
    sku: Optional[str] = Field(None, max_length=50)
    descricao: Optional[str] = None
    estoque_minimo: Optional[conint(ge=0)] = None


class ProdutoResposta(BaseModel):
    """Formato do produto na resposta da API."""

    id: int
    nome: str
    sku: Optional[str]
    descricao: Optional[str]
    estoque_atual: int
    estoque_minimo: int
    criado_em: datetime
    atualizado_em: datetime

    class Config:
        from_attributes = True


# -----------------------------------------------------------------------------
# Movimentações de estoque
# -----------------------------------------------------------------------------
class MovimentacaoCriar(BaseModel):
    """Lançamento de movimentação de estoque (entrada ou saída)."""

    produto_id: int = Field(..., description="ID do produto")
    tipo: TipoMovimentacao = Field(
        ..., description="Tipo da movimentação: entrada ou saida"
    )
    quantidade: conint(gt=0) = Field(
        ..., description="Quantidade movimentada (sempre positiva)"
    )
    observacao: Optional[str] = Field(
        default=None, description="Comentário sobre a movimentação (opcional)"
    )


class MovimentacaoResposta(BaseModel):
    """Formato da movimentação na resposta da API."""

    id: int
    produto_id: int
    tipo: str
    quantidade: int
    observacao: Optional[str]
    criado_em: datetime

    class Config:
        from_attributes = True


# -----------------------------------------------------------------------------
# Relatórios
# -----------------------------------------------------------------------------
class RelatorioEstoqueItem(BaseModel):
    """Linha do relatório de estoque atual."""

    id: int
    nome: str
    sku: Optional[str]
    estoque_atual: int
    estoque_minimo: int
    abaixo_do_minimo: bool


class ResumoEstoque(BaseModel):
    """Resumo simples de estoque para painel rápido."""

    total_produtos: int
    total_itens: int
    produtos_abaixo_minimo: int

