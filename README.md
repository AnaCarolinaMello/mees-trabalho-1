# Análise de Repositórios GitHub

## Descrição
Script Python que utiliza GraphQL para coletar dados dos 100 repositórios mais populares do GitHub, coletando métricas necessárias para responder às questões de pesquisa sobre características de repositórios populares.

## Configuração

### 1. Token do GitHub
Antes de executar o script, você precisa gerar e configurar um token pessoal do GitHub:

#### Gerar Token:
1. Acesse: GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Clique em "Generate new token (classic)"
3. Selecione as permissões necessárias:
   - `public_repo` (para acessar repositórios públicos)
   - `read:org` (para organizações)
4. Copie o token gerado

#### Configurar Token:

**Opção 1 - Variável de Ambiente:**
```bash
# Windows (cmd)
set GITHUB_TOKEN=seu_token_aqui
python main.py

# Windows (PowerShell)
$env:GITHUB_TOKEN='seu_token_aqui'
python main.py

# Linux/Mac
export GITHUB_TOKEN=seu_token_aqui
python main.py
```

**Opção 2 - Arquivo .env (recomendado):**
1. Crie um arquivo `.env` na raiz do projeto
2. Adicione a linha: `GITHUB_TOKEN=seu_token_aqui`
3. Execute normalmente: `python main.py`

Exemplo do arquivo `.env`:
```
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### 2. Dependências
Instale as dependências do projeto:

```bash
# Windows
py -m pip install -r requirements.txt

# Linux/Mac
pip install -r requirements.txt
```

Dependências utilizadas:
- `requests` - Para requisições HTTP à API do GitHub
- `json`, `csv`, `os`, `datetime`, `time` - Bibliotecas padrão do Python

## Execução
```bash
# Windows
py main.py

# Linux/Mac
python main.py
```

## Dados Coletados

O script coleta as seguintes métricas para cada repositório:

### RQ01 - Idade do Repositório
- **Campo**: `age_days`
- **Descrição**: Idade calculada em dias desde a criação

### RQ02 - Pull Requests Aceitas
- **Campo**: `merged_pull_requests`
- **Descrição**: Total de pull requests que foram aceitas (merged)

### RQ03 - Releases
- **Campo**: `total_releases`
- **Descrição**: Total de releases publicadas

### RQ04 - Última Atualização
- **Campo**: `days_since_update`
- **Descrição**: Dias desde a última atualização

### RQ05 - Linguagem Primária
- **Campo**: `primary_language`
- **Descrição**: Linguagem principal do repositório

### RQ06 - Issues Fechadas
- **Campo**: `closed_issues_ratio`
- **Descrição**: Razão entre issues fechadas e total de issues

## Saída

O script gera:
1. **Arquivo CSV**: `repositories_data.csv` com todos os dados coletados
2. **Resumo no terminal**: Estatísticas básicas dos dados coletados

## Query GraphQL Utilizada

```graphql
query {
  search(query: "stars:>1", type: REPOSITORY, first: 100) {
    pageInfo {
      hasNextPage
      endCursor
    }
    nodes {
      ... on Repository {
        name
        owner {
          login
        }
        stargazerCount
        createdAt
        updatedAt
        primaryLanguage {
          name
        }
        pullRequests(states: MERGED) {
          totalCount
        }
        releases {
          totalCount
        }
        issues {
          totalCount
        }
        issuesClosed: issues(states: CLOSED) {
          totalCount
        }
        url
        description
      }
    }
  }
}
```

## Funcionalidades Implementadas

✅ Consulta GraphQL para 100 repositórios mais populares  
✅ Coleta automática de todas as métricas necessárias  
✅ Cálculo de idade em dias  
✅ Cálculo de tempo desde última atualização  
✅ Cálculo de razão de issues fechadas  
✅ Export para CSV  
✅ Resumo estatístico  
✅ Tratamento de erros e rate limiting  
✅ Progress feedback durante coleta  

## Estrutura do CSV

```csv
name,owner,url,description,stars,age_days,days_since_update,primary_language,merged_pull_requests,total_releases,total_issues,closed_issues,closed_issues_ratio,created_at,updated_at
```