"""
API de Controle de Estoque.

Rotas REST com FastAPI que conversam com o SQLite via SQLAlchemy.
Permite:
- cadastrar produtos (CRUD)
- registrar entradas e saídas de estoque
- obter relatórios simples de estoque
"""

from pathlib import Path
from typing import Optional, Iterable
import re

from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.openapi.docs import get_swagger_ui_html
from sqlalchemy.orm import Session

import database
from database import (
    Produto as ModeloProduto,
    Movimentacao as ModeloMovimentacao,
    TipoMovimentacao,
    obter_sessao,
    criar_tabelas_se_nao_existirem,
)
from schemas import (
    ProdutoCriar,
    ProdutoAtualizar,
    ProdutoResposta,
    MovimentacaoCriar,
    MovimentacaoResposta,
    RelatorioEstoqueItem,
    ResumoEstoque,
)


# -----------------------------------------------------------------------------
# App e arquivos estáticos
# -----------------------------------------------------------------------------
app = FastAPI(
    title="API Controle de Estoque",
    version="1.0.0",
    description="CRUD de produtos, movimentações de estoque e relatórios simples.",
    docs_url=None,
    redoc_url=None,
)

pasta_static = Path(__file__).parent / "static"
if pasta_static.exists():
    app.mount("/static", StaticFiles(directory=str(pasta_static)), name="static")


# -----------------------------------------------------------------------------
# Inicialização: criar tabelas ao subir o servidor
# -----------------------------------------------------------------------------
@app.on_event("startup")
def ao_iniciar() -> None:
    """Cria as tabelas no SQLite na primeira execução e confirma o caminho do banco."""
    criar_tabelas_se_nao_existirem()
    print(f"[OK] Banco de dados conectado: {database.ARQUIVO_DO_BANCO}")


# -----------------------------------------------------------------------------
# Ajudantes
# -----------------------------------------------------------------------------
def buscar_produto_ou_404(produto_id: int, sessao: Session) -> ModeloProduto:
    """Retorna o produto pelo ID ou lança HTTP 404."""
    produto = sessao.query(ModeloProduto).filter(ModeloProduto.id == produto_id).first()
    if produto is None:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    return produto


def aplicar_movimentacao_no_estoque(
    produto: ModeloProduto, tipo: TipoMovimentacao, quantidade: int
) -> None:
    """Atualiza o estoque atual do produto conforme o tipo de movimentação."""
    if tipo == TipoMovimentacao.ENTRADA:
        produto.estoque_atual += quantidade
    else:  # SAIDA
        novo_estoque = produto.estoque_atual - quantidade
        if novo_estoque < 0:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Estoque insuficiente para saída. "
                    f"Estoque atual: {produto.estoque_atual}, saída solicitada: {quantidade}."
                ),
            )
        produto.estoque_atual = novo_estoque


def _build_relatorio_items(produtos: Iterable[ModeloProduto]) -> list[RelatorioEstoqueItem]:
    itens: list[RelatorioEstoqueItem] = []
    for p in produtos:
        abaixo = p.estoque_minimo > 0 and p.estoque_atual <= p.estoque_minimo
        itens.append(
            RelatorioEstoqueItem(
                id=p.id,
                nome=p.nome,
                sku=p.sku,
                estoque_atual=p.estoque_atual,
                estoque_minimo=p.estoque_minimo,
                abaixo_do_minimo=abaixo,
            )
        )
    return itens


# -----------------------------------------------------------------------------
# Rotas: produtos
# -----------------------------------------------------------------------------
@app.post("/produtos", response_model=ProdutoResposta)
def criar_produto(dados: ProdutoCriar, sessao: Session = Depends(obter_sessao)):
    """Cria um novo produto com estoque inicial opcional."""
    # Garante SKU único se informado
    if dados.sku:
        ja_existe = (
            sessao.query(ModeloProduto).filter(ModeloProduto.sku == dados.sku).first()
        )
        if ja_existe:
            raise HTTPException(
                status_code=400, detail="Já existe um produto com este SKU."
            )

    novo = ModeloProduto(
        nome=dados.nome,
        sku=dados.sku,
        descricao=dados.descricao,
        estoque_atual=dados.estoque_inicial,
        estoque_minimo=dados.estoque_minimo,
    )
    sessao.add(novo)
    sessao.commit()
    sessao.refresh(novo)
    return novo


@app.get("/produtos", response_model=list[ProdutoResposta])
def listar_produtos(
    com_estoque_baixo: Optional[bool] = Query(
        None,
        description=(
            "Se true, retorna apenas produtos com estoque_atual "
            "<= estoque_minimo (e estoque_minimo > 0)."
        ),
    ),
    sessao: Session = Depends(obter_sessao),
):
    """Lista produtos, com opção de filtrar apenas os com estoque abaixo do mínimo."""
    consulta = sessao.query(ModeloProduto).order_by(ModeloProduto.nome.asc())
    if com_estoque_baixo is True:
        consulta = consulta.filter(
            ModeloProduto.estoque_minimo > 0,
            ModeloProduto.estoque_atual <= ModeloProduto.estoque_minimo,
        )
    return consulta.all()


@app.get("/produtos/{produto_id}", response_model=ProdutoResposta)
def obter_produto(produto_id: int, sessao: Session = Depends(obter_sessao)):
    """Retorna um produto pelo ID."""
    return buscar_produto_ou_404(produto_id, sessao)


@app.put("/produtos/{produto_id}", response_model=ProdutoResposta)
def atualizar_produto(
    produto_id: int, dados: ProdutoAtualizar, sessao: Session = Depends(obter_sessao)
):
    """Atualiza dados do produto (apenas campos enviados)."""
    produto = buscar_produto_ou_404(produto_id, sessao)

    campos_alterados = dados.model_dump(exclude_unset=True)

    # Se for alterar SKU, garantir unicidade
    novo_sku = campos_alterados.get("sku")
    if novo_sku and novo_sku != produto.sku:
        ja_existe = (
            sessao.query(ModeloProduto)
            .filter(ModeloProduto.sku == novo_sku, ModeloProduto.id != produto.id)
            .first()
        )
        if ja_existe:
            raise HTTPException(
                status_code=400, detail="Já existe outro produto com este SKU."
            )

    for nome_campo, valor in campos_alterados.items():
        setattr(produto, nome_campo, valor)

    sessao.commit()
    sessao.refresh(produto)
    return produto


@app.delete("/produtos/{produto_id}", status_code=204)
def excluir_produto(produto_id: int, sessao: Session = Depends(obter_sessao)):
    """
    Remove o produto e suas movimentações associadas.
    Uso típico: ambiente de estudos/demonstração (não há histórico crítico).
    """
    produto = buscar_produto_ou_404(produto_id, sessao)
    sessao.delete(produto)
    sessao.commit()
    return None


# -----------------------------------------------------------------------------
# Rotas: movimentações
# -----------------------------------------------------------------------------
@app.post("/movimentacoes", response_model=MovimentacaoResposta)
def registrar_movimentacao(
    dados: MovimentacaoCriar, sessao: Session = Depends(obter_sessao)
):
    """Registra uma nova movimentação de entrada ou saída e atualiza o estoque."""
    produto = buscar_produto_ou_404(dados.produto_id, sessao)

    # Atualiza estoque com regra de negócio
    aplicar_movimentacao_no_estoque(produto, dados.tipo, dados.quantidade)

    mov = ModeloMovimentacao(
        produto_id=produto.id,
        tipo=dados.tipo.value,
        quantidade=dados.quantidade,
        observacao=dados.observacao,
    )
    sessao.add(mov)
    sessao.commit()
    sessao.refresh(mov)
    return mov


@app.get("/movimentacoes", response_model=list[MovimentacaoResposta])
def listar_movimentacoes(
    produto_id: Optional[int] = Query(
        None, description="Filtrar movimentações por ID do produto"
    ),
    tipo: Optional[TipoMovimentacao] = Query(
        None, description="Filtrar por tipo de movimentação (entrada ou saida)"
    ),
    limite: int = Query(100, ge=1, le=500, description="Quantidade máxima de registros"),
    sessao: Session = Depends(obter_sessao),
):
    """Lista movimentações de estoque, com filtros opcionais e limite de registros."""
    consulta = sessao.query(ModeloMovimentacao)
    if produto_id is not None:
        consulta = consulta.filter(ModeloMovimentacao.produto_id == produto_id)
    if tipo is not None:
        consulta = consulta.filter(ModeloMovimentacao.tipo == tipo.value)

    return (
        consulta.order_by(ModeloMovimentacao.criado_em.desc())
        .limit(limite)
        .all()
    )


# -----------------------------------------------------------------------------
# Rotas: relatórios simples
# -----------------------------------------------------------------------------
@app.get("/relatorios/estoque", response_model=list[RelatorioEstoqueItem])
def relatorio_estoque(sessao: Session = Depends(obter_sessao)):
    """
    Lista produtos com estoque atual, mínimo e flag se está abaixo do mínimo.
    Útil para um painel de acompanhamento rápido.
    """
    produtos = sessao.query(ModeloProduto).order_by(ModeloProduto.nome.asc()).all()
    return _build_relatorio_items(produtos)


@app.get("/relatorios/resumo", response_model=ResumoEstoque)
def resumo_estoque(sessao: Session = Depends(obter_sessao)):
    """
    Resumo simples de estoque:
    - quantidade de produtos
    - total de itens em estoque
    - quantos produtos estão abaixo do mínimo
    """
    produtos = sessao.query(ModeloProduto).all()
    total_produtos = len(produtos)
    total_itens = sum(p.estoque_atual for p in produtos)
    produtos_abaixo = sum(
        1
        for p in produtos
        if p.estoque_minimo > 0 and p.estoque_atual <= p.estoque_minimo
    )
    return ResumoEstoque(
        total_produtos=total_produtos,
        total_itens=total_itens,
        produtos_abaixo_minimo=produtos_abaixo,
    )


# -----------------------------------------------------------------------------
# Rotas auxiliares
# -----------------------------------------------------------------------------
@app.get("/")
def raiz():
    """Indica onde estão a documentação e a interface de teste."""
    return {
        "api": "Controle de Estoque",
        "docs": "/docs",
        "interface": "/static/index.html",
    }


@app.get("/docs", include_in_schema=False)
def documentacao_swagger():
    """Documentação Swagger com barra para voltar à página principal."""
    html = get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=app.title + " — Swagger UI",
    )
    body = html.body.decode() if isinstance(html.body, bytes) else html.body
    barra = (
        '<div style="padding:10px 16px;background:#0ea5e9;">'
        '<a href="/static/index.html" '
        'style="color:#fff;text-decoration:none;font-weight:600;">'
        "← Voltar à página principal</a></div>"
    )
    body_novo = re.sub(r"<body[^>]*>", r"\g<0>" + barra, body, count=1)
    return HTMLResponse(content=body_novo)


@app.get("/db-status")
def status_do_banco(sessao: Session = Depends(obter_sessao)):
    """Confirma a conexão com o SQLite e informa alguns números do estoque."""
    total_produtos = sessao.query(ModeloProduto).count()
    total_movs = sessao.query(ModeloMovimentacao).count()
    total_itens = (
        sessao.query(ModeloProduto.estoque_atual).all()
    )  # lista de tuplas (valor,)
    soma_itens = sum(v[0] for v in total_itens)
    return {
        "banco": "SQLite",
        "arquivo": str(database.ARQUIVO_DO_BANCO),
        "tabelas": ["produtos", "movimentacoes"],
        "total_produtos": total_produtos,
        "total_movimentacoes": total_movs,
        "total_itens_estoque": soma_itens,
    }

