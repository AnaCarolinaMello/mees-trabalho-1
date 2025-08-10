import requests
import json
import csv
import os
from datetime import datetime
import time

class GitHubAnalyzer:
    def __init__(self, token):
        """
        Inicializa o analisador com token de acesso do GitHub
        """
        self.token = token
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        self.base_url = "https://api.github.com/graphql"
    
    def create_graphql_query(self, cursor=None):
        """
        Cria a query GraphQL para buscar os repositórios mais populares
        """
        after_clause = f', after: "{cursor}"' if cursor else ""
        
        query = f"""
        query {{
            search(query: "stars:>5000", type: REPOSITORY, first: 20{after_clause}) {{
                pageInfo {{
                    hasNextPage
                    endCursor
                }}
                nodes {{
                    ... on Repository {{
                        name
                        owner {{
                            login
                        }}
                        stargazerCount
                        createdAt
                        updatedAt
                        primaryLanguage {{
                            name
                        }}
                        pullRequests(states: MERGED) {{
                            totalCount
                        }}
                        releases {{
                            totalCount
                        }}
                        issues {{
                            totalCount
                        }}
                        issuesClosed: issues(states: CLOSED) {{
                            totalCount
                        }}
                        url
                        description
                    }}
                }}
            }}
        }}
        """
        return query
    
    def make_request(self, query):
        """
        Faz a requisição GraphQL para a API do GitHub
        """
        payload = {"query": query}
        
        try:
            response = requests.post(
                self.base_url,
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 401:
                print("ERRO: Token inválido ou expirado!")
                print("Verifique se seu token GitHub está correto e tem as permissões necessárias.")
                return None
            elif response.status_code == 403:
                print("ERRO: Rate limit atingido ou permissões insuficientes!")
                print("Aguarde alguns minutos ou verifique as permissões do token.")
                return None
            elif response.status_code >= 500:
                print(f"ERRO: Problema temporário no servidor GitHub (Código {response.status_code})")
                print("Tente novamente em alguns minutos.")
                return None
            else:
                print(f"Erro na requisição: {response.status_code}")
                print(f"Resposta: {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"Erro de conexão: {e}")
            return None
    
    def calculate_age_days(self, created_at):
        """
        Calcula a idade do repositório em dias
        """
        created_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        current_date = datetime.now(created_date.tzinfo)
        return (current_date - created_date).days
    
    def calculate_days_since_update(self, updated_at):
        """
        Calcula quantos dias desde a última atualização
        """
        updated_date = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
        current_date = datetime.now(updated_date.tzinfo)
        return (current_date - updated_date).days
    
    def calculate_closed_issues_ratio(self, total_issues, closed_issues):
        """
        Calcula a razão de issues fechadas
        """
        if total_issues == 0:
            return 0.0
        return closed_issues / total_issues
    
    def process_repository_data(self, repo):
        """
        Processa os dados de um repositório individual
        """
        return {
            'name': repo['name'],
            'owner': repo['owner']['login'],
            'url': repo['url'],
            'description': repo['description'] or "",
            'stars': repo['stargazerCount'],
            'age_days': self.calculate_age_days(repo['createdAt']),
            'days_since_update': self.calculate_days_since_update(repo['updatedAt']),
            'primary_language': repo['primaryLanguage']['name'] if repo['primaryLanguage'] else "Unknown",
            'merged_pull_requests': repo['pullRequests']['totalCount'],
            'total_releases': repo['releases']['totalCount'],
            'total_issues': repo['issues']['totalCount'],
            'closed_issues': repo['issuesClosed']['totalCount'],
            'closed_issues_ratio': self.calculate_closed_issues_ratio(
                repo['issues']['totalCount'], 
                repo['issuesClosed']['totalCount']
            ),
            'created_at': repo['createdAt'],
            'updated_at': repo['updatedAt']
        }
    
    def collect_repositories_data(self, limit=100):
        """
        Coleta dados dos repositórios mais populares
        """
        repositories = []
        cursor = None
        collected = 0
        
        print(f"Iniciando coleta de dados para {limit} repositórios...")
        
        while collected < limit:
            query = self.create_graphql_query(cursor)
            response_data = self.make_request(query)
            
            if not response_data or 'data' not in response_data:
                print("Erro ao obter dados da API")
                break
            
            search_results = response_data['data']['search']
            repos = search_results['nodes']
            
            for repo in repos:
                if collected >= limit:
                    break
                    
                try:
                    processed_repo = self.process_repository_data(repo)
                    repositories.append(processed_repo)
                    collected += 1
                    
                    if collected % 10 == 0:
                        print(f"Coletados {collected}/{limit} repositórios...")
                        
                except Exception as e:
                    print(f"Erro ao processar repositório {repo.get('name', 'Unknown')}: {e}")
                    continue
            
            # Verifica se há mais páginas
            if not search_results['pageInfo']['hasNextPage'] or collected >= limit:
                break
                
            cursor = search_results['pageInfo']['endCursor']
            
            # Rate limiting - pausa entre requisições
            time.sleep(3)
        
        print(f"Coleta finalizada. Total coletado: {len(repositories)} repositórios")
        return repositories
    
    def save_to_csv(self, repositories, filename="repositories_data.csv"):
        """
        Salva os dados dos repositórios em arquivo CSV
        """
        if not repositories:
            print("Nenhum dado para salvar")
            return
        
        fieldnames = [
            'name', 'owner', 'url', 'description', 'stars',
            'age_days', 'days_since_update', 'primary_language',
            'merged_pull_requests', 'total_releases', 'total_issues',
            'closed_issues', 'closed_issues_ratio', 'created_at', 'updated_at'
        ]
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(repositories)
        
        print(f"Dados salvos em {filename}")
    
    def print_summary(self, repositories):
        """
        Imprime um resumo dos dados coletados
        """
        if not repositories:
            return
        
        print("\n" + "="*50)
        print("RESUMO DOS DADOS COLETADOS")
        print("="*50)
        
        print(f"Total de repositórios: {len(repositories)}")
        
        # Estatísticas básicas
        ages = [repo['age_days'] for repo in repositories]
        stars = [repo['stars'] for repo in repositories]
        prs = [repo['merged_pull_requests'] for repo in repositories]
        releases = [repo['total_releases'] for repo in repositories]
        
        print(f"\nIdade dos repositórios:")
        print(f"  Mediana: {sorted(ages)[len(ages)//2]} dias")
        print(f"  Mínima: {min(ages)} dias")
        print(f"  Máxima: {max(ages)} dias")
        
        print(f"\nEstrelas:")
        print(f"  Mediana: {sorted(stars)[len(stars)//2]:,}")
        print(f"  Mínima: {min(stars):,}")
        print(f"  Máxima: {max(stars):,}")
        
        print(f"\nPull Requests aceitas:")
        print(f"  Mediana: {sorted(prs)[len(prs)//2]:,}")
        print(f"  Máximo: {max(prs):,}")
        
        print(f"\nReleases:")
        print(f"  Mediana: {sorted(releases)[len(releases)//2]:,}")
        print(f"  Máximo: {max(releases):,}")
        
        # Linguagens mais populares
        languages = {}
        for repo in repositories:
            lang = repo['primary_language']
            languages[lang] = languages.get(lang, 0) + 1
        
        print(f"\nTop 10 linguagens:")
        sorted_langs = sorted(languages.items(), key=lambda x: x[1], reverse=True)
        for lang, count in sorted_langs[:10]:
            print(f"  {lang}: {count} repositórios")


def load_env_file():
    """
    Carrega variáveis de ambiente de um arquivo .env (opcional)
    """
    try:
        if os.path.exists('.env'):
            with open('.env', 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key.strip()] = value.strip()
    except Exception as e:
        pass  # Se houver erro ao ler .env, continua sem ele


def main():
    """
    Função principal do programa
    """
    # Carrega arquivo .env se existir
    load_env_file()
    
    # Obtém o token do GitHub da variável de ambiente
    token = os.getenv('GITHUB_TOKEN')
    
    if not token:
        print("ERRO: Token do GitHub não encontrado!")
        return
    
    # Inicializa o analisador
    analyzer = GitHubAnalyzer(token)
    
    # Coleta dados dos 100 repositórios mais populares
    repositories = analyzer.collect_repositories_data(limit=100)
    
    if repositories:
        # Salva os dados em CSV
        analyzer.save_to_csv(repositories)
        
        # Mostra resumo
        analyzer.print_summary(repositories)
        
        print("\n" + "="*50)
        print("MÉTRICAS PARA AS QUESTÕES DE PESQUISA:")
        print("="*50)
        print("RQ01 - Idade: campo 'age_days'")
        print("RQ02 - Pull Requests aceitas: campo 'merged_pull_requests'")
        print("RQ03 - Releases: campo 'total_releases'")
        print("RQ04 - Última atualização: campo 'days_since_update'")
        print("RQ05 - Linguagem: campo 'primary_language'")
        print("RQ06 - Issues fechadas: campo 'closed_issues_ratio'")
    else:
        print("Falha na coleta de dados.")


if __name__ == "__main__":
    main()
