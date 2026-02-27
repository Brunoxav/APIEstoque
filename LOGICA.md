# Como tudo funciona — Sistema de Controle de Estoque

Este texto explica o Projeto 2 de um jeito direto: o que cada parte faz, como as peças se conversam e onde entra a tal “lógica de negócio”.

---

## A ideia geral

Quando você cadastra um produto, registra uma **entrada** de estoque ou lança uma **saída**, acontece a seguinte corrente:

```
Você na tela  →  API (FastAPI)  →  Banco (SQLite)
     ↑                 ↑                 ↑
  formulários      rotas /produtos,   arquivo .db
                 /movimentacoes...   (estoque.db)
```

A interface HTML manda requisições HTTP para a API.  
A API usa o SQLAlchemy para falar com o SQLite (`estoque.db`).  
Toda a lógica de estoque — atualizar quantidade, impedir saída acima do disponível, marcar produtos com estoque baixo — acontece no servidor.

---

## 1. O banco de dados (`database.py`)

Este arquivo define:

- Onde o banco fica (`estoque.db` na pasta do projeto)
- As tabelas
  - `produtos`
  - `movimentacoes`
- O enum para tipo de movimentação (`entrada` ou `saida`)

### Tabela `produtos`

Cada linha representa um item do estoque. Campos principais:

- `id`: identificador numérico
- `nome`: nome do produto (obrigatório)
- `sku`: código interno / SKU (opcional, mas único se preenchido)
- `descricao`: texto livre
- `estoque_atual`: quantidade atual em estoque
- `estoque_minimo`: quantidade mínima que você considera “segura”
- `criado_em` / `atualizado_em`: datas de criação e última atualização

### Tabela `movimentacoes`

Aqui ficam os lançamentos de entrada e saída. Campos principais:

- `id`: identificador da movimentação
- `produto_id`: qual produto foi movimentado
- `tipo`: `entrada` ou `saida`
- `quantidade`: sempre um número inteiro positivo
- `observacao`: comentário livre (ex.: “Compra do fornecedor X”)
- `criado_em`: quando a movimentação foi registrada

Cada movimentação também está ligada a um produto via `relationship`, o que permite navegar de um produto para suas movimentações (`produto.movimentacoes`).

### Sessão e conexão

Assim como no Projeto 1:

- Existe um `engine` apontando para o arquivo SQLite
- `SessaoLocal` entrega uma sessão para cada requisição
- A função `obter_sessao()` usa `yield`: o FastAPI chama, a rota usa a sessão e, no final, ela é fechada automaticamente

---

## 2. Os contratos da API (`schemas.py`)

Os schemas Pydantic definem o formato do que entra e sai da API.  
Isso garante validação automática e documentação clara em `/docs`.

### Produtos

- **`ProdutoCriar`**
  - Campos obrigatórios: `nome`
  - Campos opcionais: `sku`, `descricao`
  - `estoque_inicial`: começa em 0 se não informado
  - `estoque_minimo`: define a partir de quanto o estoque é considerado baixo

- **`ProdutoAtualizar`**
  - Todos os campos opcionais
  - Só o que vier no body será alterado (PUT parcial)

- **`ProdutoResposta`**
  - Como o produto é devolvido em JSON
  - Inclui `estoque_atual`, `estoque_minimo` e datas

### Movimentações

- **`MovimentacaoCriar`**
  - `produto_id`: ID do produto
  - `tipo`: enum `entrada` ou `saida`
  - `quantidade`: inteiro > 0 (validação no schema)
  - `observacao`: opcional

- **`MovimentacaoResposta`**
  - Representa o registro gravado no banco, com data e ID

### Relatórios

- **`RelatorioEstoqueItem`**
  - Linha do relatório de estoque: produto, estoque atual, mínimo e flag `abaixo_do_minimo`

- **`ResumoEstoque`**
  - Números simples para um painel:
    - `total_produtos`
    - `total_itens`
    - `produtos_abaixo_minimo`

---

## 3. A API em si (`main.py`)

Aqui ficam as rotas que recebem os pedidos, conversam com o banco e devolvem respostas JSON.

### Inicialização

Na subida do servidor:

- `criar_tabelas_se_nao_existirem()` garante que `produtos` e `movimentacoes` existam
- Um `print` mostra o caminho do arquivo `estoque.db` no terminal

### Funções ajudantes

- **`buscar_produto_ou_404`**
  - Centraliza a lógica “busca produto por ID ou retorna 404”

- **`aplicar_movimentacao_no_estoque`**
  - Contém a lógica de negócio principal:
    - Se for `entrada`, soma a quantidade ao `estoque_atual`
    - Se for `saida`, tenta subtrair; se ficar negativo, lança HTTP 400 com mensagem clara

- **`_build_relatorio_items`**
  - Constrói os itens do relatório de estoque, incluindo o campo `abaixo_do_minimo`

### Rotas de produtos

Em uma linha:

- `POST /produtos`
  - Cria um novo produto
  - Se o SKU for informado, verifica se já existe outro igual
  - Permite iniciar com `estoque_inicial` > 0

- `GET /produtos`
  - Lista produtos
  - Se `com_estoque_baixo=true`, filtra apenas os que estão com `estoque_atual <= estoque_minimo` (e `estoque_minimo > 0`)

- `GET /produtos/{id}`
  - Devolve um produto ou 404

- `PUT /produtos/{id}`
  - Atualiza apenas os campos enviados no body
  - Garante que o novo SKU (se enviado) não seja duplicado em outro produto

- `DELETE /produtos/{id}`
  - Remove o produto e suas movimentações associadas
  - Pensado para ambiente de estudo/demonstração (não crítico em termos de histórico)

### Rotas de movimentações

- `POST /movimentacoes`
  - Recebe `produto_id`, `tipo` (entrada/saida), `quantidade` e `observacao`
  - Busca o produto pelo ID
  - Chama `aplicar_movimentacao_no_estoque` para atualizar o estoque
  - Grava a movimentação na tabela `movimentacoes`

- `GET /movimentacoes`
  - Lista o histórico
  - Filtros opcionais:
    - `produto_id`
    - `tipo` (`entrada` ou `saida`)
    - `limite` (padrão 100, máximo 500)
  - Ordena do mais recente para o mais antigo

### Rotas de relatórios

- `GET /relatorios/estoque`
  - Percorre todos os produtos
  - Para cada um, monta um item com:
    - `estoque_atual`
    - `estoque_minimo`
    - `abaixo_do_minimo` (true/false)
  - Usado pela interface para destacar produtos críticos

- `GET /relatorios/resumo`
  - Calcula:
    - `total_produtos`
    - `total_itens` (soma de `estoque_atual` de todos os produtos)
    - `produtos_abaixo_minimo`

### Rotas auxiliares

- `GET /`
  - Indica os caminhos de `/docs` e `/static/index.html`

- `GET /docs`
  - Mesma ideia do Projeto 1: documentação Swagger com uma barrinha azul para voltar à interface HTML

- `GET /db-status`
  - Mostra:
    - caminho do `estoque.db`
    - quantidade de produtos
    - quantidade de movimentações
    - total de itens somados no estoque

---

## 4. A interface no navegador (`static/index.html`)

A página HTML foi pensada para testar a API confortavelmente, com um layout moderno e organizado em seções:

- **Cadastrar produto**
  - Formulário com nome, descrição, SKU, estoque inicial e mínimo
  - Chama `POST /produtos`

- **Produtos cadastrados**
  - Lista os produtos com:
    - Nome e descrição
    - Estoque atual e mínimo
    - Badges de:
      - SKU (se existir)
      - Situação do estoque (OK ou “Estoque baixo”)
  - Botões rápidos:
    - “Usar para movimentar” → joga o ID no formulário de movimentação
    - “Editar” → preenche a seção de edição com os dados do produto

- **Movimentar estoque**
  - Campos:
    - ID do produto
    - Tipo: entrada/saída
    - Quantidade
    - Observação
  - Chama `POST /movimentacoes`
  - Após sucesso, atualiza lista de produtos e histórico

- **Histórico de movimentações**
  - Filtros:
    - ID do produto (opcional)
    - Tipo (todas / apenas entradas / apenas saídas)
    - Limite de registros
  - Chama `GET /movimentacoes`

- **Relatórios rápidos**
  - Botões que chamam:
    - `GET /relatorios/estoque` → lista de produtos com situação do estoque
    - `GET /relatorios/resumo` → cards com números gerais

- **Editar / excluir produto**
  - Permite:
    - Carregar os dados atuais de um produto (chama `GET /produtos/{id}`)
    - Enviar alterações (chama `PUT /produtos/{id}`)
    - Excluir o produto (chama `DELETE /produtos/{id}`)

Em todas as ações, a página usa `fetch()` para conversar com a API, mostra mensagens de sucesso/erro e atualiza as listas visíveis.

---

## Por onde começar a ler o código

Uma ordem sugerida para entender o projeto:

1. **`database.py`** — ver como as tabelas de produtos e movimentações são definidas e como a sessão é criada
2. **`schemas.py`** — entender o formato dos dados de entrada/saída e dos relatórios
3. **`main.py`** — seguir o fluxo de:
   - cadastro de produto
   - movimentação de estoque
   - geração dos relatórios
4. **`static/index.html`** — ver como cada seção da tela usa a API

Assim você enxerga a corrente completa: da tela, passando pela lógica de negócio, até o banco de dados.

