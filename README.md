# Projeto 2 — Sistema de Controle de Estoque

API REST para controle de estoque com FastAPI e SQLite.

Permite cadastrar produtos, registrar entradas/saídas de estoque e gerar relatórios simples — tudo no mesmo estilo do Projeto 1 (Chamados de Suporte), mas agora voltado para estoque.

## Funcionalidades

- **Cadastro de produtos**  
  - Nome, descrição, SKU/código interno  
  - Estoque inicial opcional  
  - Estoque mínimo para alerta

- **Movimentações de estoque**  
  - **Entrada**: aumenta o estoque do produto  
  - **Saída**: reduz o estoque (com validação para não ficar negativo)  
  - Histórico das movimentações por produto, com data, tipo e observação

- **Relatórios simples**  
  - Estoque atual por produto, indicando se está **abaixo do mínimo**  
  - Resumo geral: total de produtos, total de itens, quantos estão abaixo do mínimo

O que demonstra:

- **CRUD** completo de produtos
- **Lógica de negócio** para atualizar estoque e impedir saída acima do disponível
- **Banco de dados** com 2 tabelas (produtos e movimentações)

## Como rodar

```bash
cd projeto2_estoque
pip install -r requirements.txt
uvicorn main:app --reload
```

Acesse:

- **API**: `http://127.0.0.1:8000`
- **Interface de teste**: `http://127.0.0.1:8000/static/index.html`
- **Documentação Swagger**: `http://127.0.0.1:8000/docs`

## Endpoints principais

### Produtos

- `POST /produtos` — Cadastrar produto
- `GET /produtos` — Listar produtos (`com_estoque_baixo=true` para filtrar)
- `GET /produtos/{id}` — Buscar produto por ID
- `PUT /produtos/{id}` — Atualizar produto (parcial)
- `DELETE /produtos/{id}` — Excluir produto e suas movimentações

### Movimentações

- `POST /movimentacoes` — Registrar **entrada** ou **saída**  
  - Corpo: `produto_id`, `tipo` (`entrada` ou `saida`), `quantidade`, `observacao` (opcional)
- `GET /movimentacoes` — Listar movimentações  
  - Filtros: `produto_id`, `tipo`, `limite`

### Relatórios

- `GET /relatorios/estoque` — Estoque atual por produto (e se está abaixo do mínimo)
- `GET /relatorios/resumo` — Resumo geral do estoque

### Status do banco

- `GET /db-status` — Informa caminho do arquivo SQLite e alguns números do estoque



