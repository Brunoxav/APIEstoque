Projeto 2 — Sistema de Controle de Estoque

API REST desenvolvida com FastAPI e SQLite para controle de estoque. O sistema permite cadastrar produtos, registrar entradas e saídas e gerar relatórios simples, seguindo o mesmo padrão do Projeto 1 (Chamados de Suporte), mas aplicado ao contexto de estoque.

Visão geral

O objetivo deste projeto é simular um sistema básico de gestão de estoque, com regras reais de negócio e organização de dados em banco relacional.

Principais funcionalidades
Cadastro de produtos

Nome, descrição e SKU/código interno

Definição de estoque inicial (opcional)

Configuração de estoque mínimo para alertas

Movimentações de estoque

Entrada de itens, aumentando o saldo disponível

Saída de itens, com validação para impedir estoque negativo

Histórico completo por produto, incluindo data, tipo e observações

Relatórios simples

Consulta do estoque atual por produto, indicando quando está abaixo do mínimo

Resumo geral com:

Total de produtos cadastrados

Quantidade total em estoque

Itens abaixo do nível mínimo

O que este projeto demonstra

Implementação de CRUD completo para produtos

Regras de negócio para controle de estoque

Validação de dados no backend

Modelagem com duas tabelas principais (produtos e movimentações)

Como executar o projeto
cd projeto2_estoque
pip install -r requirements.txt
uvicorn main:app --reload

Após iniciar o servidor, acesse:

API local: http://127.0.0.1:8000

Interface simples de testes: http://127.0.0.1:8000/static/index.html

Documentação interativa (Swagger): http://127.0.0.1:8000/docs

Endpoints principais
Produtos

POST /produtos — Cadastrar produto

GET /produtos — Listar produtos (filtro opcional com_estoque_baixo=true)

GET /produtos/{id} — Buscar produto por ID

PUT /produtos/{id} — Atualizar produto

DELETE /produtos/{id} — Remover produto e movimentações associadas

Movimentações

POST /movimentacoes — Registrar entrada ou saída
Campos esperados: produto_id, tipo (entrada ou saida), quantidade e observacao (opcional)

GET /movimentacoes — Listar movimentações
Filtros disponíveis: produto_id, tipo e limite

Relatórios

GET /relatorios/estoque — Lista o estoque atual por produto e alerta de mínimo

GET /relatorios/resumo — Retorna um resumo geral do estoque

Status do banco

GET /db-status — Mostra o caminho do arquivo SQLite e informações gerais do banco
