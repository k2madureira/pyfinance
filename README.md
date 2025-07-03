# Pyfinance 
 - Cotações
diárias de ativos financeiros e permita o acesso a métricas relevantes

### Structure:

```
  pyfinance
    |_ venv
    |_ api_root
    |_ api_rest
        |_ migrations
        |_ models
            |_ quote
            |_ ticker
        |_ serializers
            |_ quote
            |_ ticker
        |_ urls
            |_ quote
            |_ ticker
        |_ utls
            |_ handling
            |_ search_ticker
        |_ views
            |_ quote
            |_ ticker
```

### Data schema:
![Image](https://github.com/user-attachments/assets/aedeba4f-b7fb-4141-ae6c-9812189ae7a7)



## Setting up local environment:

#### 1. Clonar o Repositório e Navegar para o Projeto
 - git clone https://github.com/k2madureira/pyfinance.git
 - cd pyfinance

#### 2. Configurar o Ambiente Python (Virtual Environment)

 - Para Windows:
```
  python -m venv venv
  .\venv\Scripts\activate
```
- Para Linux/macOS:
```
  python3 -m venv venv
  source venv/bin/activate
```
#### 3. Instalar Dependências Python
```
 pip install -r requirements.txt
```
#### 4. Configurar Variáveis de Ambiente

- Crie um arquivo chamado *.env* na raiz do projeto e adicione suas variáveis.

#### 5. Configurar e Migrar o Banco de Dados Django
```
 python manage.py makemigrations
 python manage.py migrate
```
#### 6. Iniciar o Servidor Django (API REST)
```
python manage.py runserver
```


### Endpoints:

|Number| Type | Route | Definition |
|-|------|-------|------------|
|1| *Get* | /tickers | Listagem de tickers |
|2| *Get* | /tickers/**id** | Detalhamento de ticker |
|3| *Get* | /tickers/load | Carga de tickers no BD |
|4| *Get* | /tickers/**id**/quotes | Listagem de quotes por ticker |
|4| *Get* | /quotes/ | Listagem de quotes |


### Endpoints Params:

* Observacao: A busca dos dados atualizados dos tickets e realizado no detalhamento, por conta da limitacao de requisicoes da API do alphavantage.

1. GET => http://127.0.0.1:8000/api/v1/tickers?

    query strings:
      - perPage=1 
      - page=3 
      - symbol=A 
      - symbol=AAA 
      - symbol=AMZN

2. GET => http://127.0.0.1:8000/api/v1/tickers/{SYMBOL}

    query strings:
      - sma_days=5 
      - sma_days_volume=50 
      - mult_atypical=2 
      - rsi_days=2 
      - start_date=2025-06-01 
      - end_date=2025-06-12 
      - total_days=50 
      - threshold=2
  

3. GET => http://127.0.0.1:8000/api/v1/tickers/load (carrega todas os tickers no BD)

#### Local Exemple:


1. http://127.0.0.1:8000/api/v1/tickers



