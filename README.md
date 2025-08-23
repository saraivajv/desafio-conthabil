# Desafio Técnico Conthabil - Automação e API de Diários Oficiais

![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python)
![Django](https://img.shields.io/badge/Django-5.2-092E20?style=for-the-badge&logo=django)
![Django REST Framework](https://img.shields.io/badge/DRF-3.14-A30000?style=for-the-badge&logo=django)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-4169E1?style=for-the-badge&logo=postgresql)
![Docker](https://img.shields.io/badge/Docker-20.10-2496ED?style=for-the-badge&logo=docker)
![Selenium](https://img.shields.io/badge/Selenium-4.10-43B02A?style=for-the-badge&logo=selenium)

## 📖 Visão Geral do Projeto

Este projeto consiste em um sistema de automação (ETL) que realiza a extração de publicações do Diário Oficial do Município de Natal/RN. Os documentos (PDFs) são coletados, enviados para um serviço de hospedagem de arquivos e, por fim, suas URLs públicas são armazenadas em um banco de dados PostgreSQL, acessível através de uma API REST.

A aplicação foi totalmente containerizada com Docker para garantir a portabilidade e a facilidade de execução em qualquer ambiente, e o deploy foi realizado na plataforma **Render**.

## ✨ Funcionalidades Principais

-   **Coleta Automatizada**: Um script Python com **Selenium** acessa o site do DOM, filtra as publicações do mês anterior e baixa os PDFs.
-   **Upload de Arquivos**: Os PDFs coletados são enviados para o serviço [0x0.st](https://0x0.st) via requisições HTTP.
-   **API REST**: Uma API construída com **Django** e **Django REST Framework** para armazenar e consultar as URLs dos documentos.
-   **Consulta e Filtragem**: A API permite listar todas as publicações e filtrá-las por competência (mês/ano).
-   **Ambiente Containerizado**: A API e o banco de dados são orquestrados com **Docker Compose**, facilitando o ambiente de desenvolvimento.
-   **Deploy na Nuvem**: A aplicação está em produção e disponível publicamente através da plataforma **Render**.

## 🚀 API em Produção

A API está disponível publicamente no seguinte endereço:

**URL Base:** `https://conthabil-api.onrender.com`

### Endpoints Principais:

-   **Listar todas as publicações:**
    `GET /api/publications/`
-   **Filtrar publicações por competência (ex: Julho de 2025):**
    `GET /api/publications/?competence=2025-07`

## 🛠️ Tecnologias Utilizadas

-   **Backend:** Django, Django REST Framework
-   **Banco de Dados:** PostgreSQL
-   **Automação e Coleta:** Python, Selenium, Requests, BeautifulSoup
-   **Containerização:** Docker, Docker Compose
-   **Servidor de Produção:** Gunicorn, Whitenoise
-   **Plataforma de Deploy (PaaS):** Render

## 📂 Estrutura do Projeto

```
.
├── coletor.py         # Script de automação para coleta e upload
├── Dockerfile         # Define a imagem Docker da API Django
├── docker-compose.yml # Orquestra os serviços da API e do banco de dados
├── entrypoint.sh      # Script de inicialização do contêiner em produção
├── requirements.txt   # Lista de dependências Python
└── src/
    ├── manage.py      # Utilitário de gerenciamento do Django
    ├── config/        # Configurações do projeto Django (settings.py, urls.py)
    └── publications/  # App Django com models, views e serializers
```

## ⚙️ Como Executar o Projeto Localmente

Para rodar este projeto em seu ambiente local, siga os passos abaixo.

### Pré-requisitos

-   Git
-   Docker
-   Docker Compose

### 1. Clonar o Repositório

```bash
git clone https://github.com/saraivajv/desafio-conthabil.git
cd desafio-conthabil
```

### 2. Configurar Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto. Este arquivo será usado tanto pelo Docker Compose (para configurar a API) quanto pelo script `coletor.py` (rodando localmente).

Copie o seguinte conteúdo para o seu `.env`:

```ini
# .env (para ambiente de desenvolvimento local com Docker)

# --- Configurações do Django ---
# Estas variáveis são injetadas no contêiner 'api' pelo docker-compose.yml

SECRET_KEY='django-insecure-local-development-key-!@#$%^'
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
# ATENÇÃO: O host é 'db', que é o nome do serviço do PostgreSQL no docker-compose.yml.
DATABASE_URL="postgres://conthabil_user:strongpassword123@db:5432/conthabil_db"


# --- Configurações do Coletor ---
# Estas variáveis são lidas pelo script coletor.py quando executado na sua máquina.

PROJECT_DOWNLOADS_FOLDER_NAME=downloads
DOM_URL="https://www.natal.rn.gov.br/dom"
UPLOAD_URL="https://0x0.st"
# Endpoint da API rodando localmente no Docker.
API_ENDPOINT="http://127.0.0.1:8000/api/publications/"
```

### 3. Subir os Contêineres

Use o Docker Compose para construir as imagens e iniciar os serviços da API e do banco de dados.

```bash
docker compose up --build -d
```
A API estará acessível em `http://localhost:8000/api/publications/`.

### 4. Executar o Script Coletor

Para popular o banco de dados, execute o script `coletor.py`. É recomendado usar um ambiente virtual Python para isso.

```bash
# Crie e ative um ambiente virtual
python -m venv venv
source venv/bin/activate

# Instale as dependências
pip install -r requirements.txt

# Execute o script
python coletor.py
```
Após a execução, os dados estarão disponíveis na API.

## 📝 Documentação da API

### `GET /api/publications/`
Retorna uma lista de todas as publicações armazenadas.

-   **Método:** `GET`
-   **Resposta de Sucesso (200 OK):**
    ```json
    [
        {
            "id": 1,
            "file_url": "https://0x0.st/exemplo-url-1.pdf",
            "competence": "2025-07",
            "created_at": "2025-08-23T03:00:00Z"
        },
        {
            "id": 2,
            "file_url": "https://0x0.st/exemplo-url-2.pdf",
            "competence": "2025-07",
            "created_at": "2025-08-23T03:00:05Z"
        }
    ]
    ```

### `GET /api/publications/?competence=<AAAA-MM>`
Retorna uma lista de publicações filtrada pela competência informada.

-   **Método:** `GET`
-   **Parâmetro de URL:** `competence` (string, formato `AAAA-MM`)
-   **Exemplo:** `/api/publications/?competence=2025-07`
-   **Resposta de Sucesso (200 OK):** Uma lista (potencialmente vazia) de objetos de publicação que correspondem ao filtro.

### `POST /api/publications/`
Cria um novo registro de publicação. Este endpoint é usado pelo `coletor.py`.

-   **Método:** `POST`
-   **Corpo da Requisição (JSON):**
    ```json
    {
        "file_url": "https://0x0.st/nova-url.pdf",
        "competence": "2025-07"
    }
    ```
-   **Resposta de Sucesso (201 Created):**
    ```json
    {
        "id": 3,
        "file_url": "https://0x0.st/nova-url.pdf",
        "competence": "2025-07",
        "created_at": "2025-08-23T03:00:10Z"
    }
    ```

## 🔗 Autor

-   **Nome:** João Victor G. de A. Saraiva
