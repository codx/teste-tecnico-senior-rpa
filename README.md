# RPA Scraper Project - Senior Challenge

Este projeto é um sistema de coleta de dados (web scraping) distribuído de alta performance e resiliência, utilizando **FastAPI** para a API, **RabbitMQ** para o gerenciamento assíncrono de tarefas (jobs), **PostgreSQL** para persistência e **Selenium/BeautifulSoup** para o processo de scraping.

A solução foi desenvolvida seguindo padrões de engenharia de software de nível **Sênior**, priorizando **SOLID**, **resiliência**, **validação de dados** e **testabilidade**.

---

## 🏗️ Arquitetura do Sistema

O sistema é composto por cinco componentes principais desacoplados:

1.  **API (FastAPI):** Gateway de entrada que recebe solicitações de scraping, cria registros de jobs no banco e publica mensagens no RabbitMQ.
2.  **Queue (RabbitMQ):** Message Broker que garante o desacoplamento entre a API e o processamento pesado de scraping.
3.  **Worker:** Consumidor assíncrono que processa as mensagens da fila e orquestra a execução dos scrapers.
4.  **Scrapers Engine:**
    *   **HockeyScraper:** Extração estática rápida utilizando BeautifulSoup4 com paginação.
    *   **OscarScraper:** Extração dinâmica robusta utilizando Selenium, com tratamento de AJAX e elementos dinâmicos (Stale Elements).
5.  **PostgreSQL:** Banco de dados relacional para persistência do status dos jobs e dos dados coletados, com suporte a `ON CONFLICT` para garantir idempotência e gerenciado via **Alembic Migrations**.

---

## 🛠️ Funcionalidades Implementadas

*   **Resiliência de Mensageria:** Pool de conexões RabbitMQ (`RabbitMQManager` Singleton) com suporte a **Dead Letter Queue (DLQ)** para tratamento de falhas e auditoria.
*   **Gestão de Banco de Dados:** Uso de **Alembic** para versionamento de schema e migrações controladas.
*   **Observabilidade:** Logs estruturados em **JSON** para integração com stacks de monitoramento modernas (ELK/Loki).
*   **Healthchecks Avançados:** Endpoint `/health` que verifica a saúde real das dependências (DB e RabbitMQ).
*   **Evasão de Bloqueios:** Uso de **User-Agents rotativos** e cabeçalhos dinâmicos nos scrapers para evitar detecção.
*   **Migrations Automáticas:** Aplicação automática de migrações do banco de dados no startup via Docker Compose.
*   **Tratamento de Stale Elements:** Lógica robusta no `OscarScraper` para lidar com elementos dinâmicos do Selenium que desaparecem do DOM.
*   **Idempotência:** Camada de persistência utiliza `ON CONFLICT` para garantir que reprocessamentos não dupliquem dados.

---

## 🚀 Como Instalar e Rodar (Docker)

A infraestrutura completa é containerizada e pode ser iniciada com um único comando:

1.  **Clone o repositório:**
    ```bash
    git clone <url-do-repositorio>
    cd teste-tecnico-senior-rpa
    ```

2.  **Suba os containers:**
    ```bash
    docker-compose up --build
    ```

### Serviços iniciados:
*   **API:** `http://localhost:8000` (Swagger: `/docs`)
*   **PostgreSQL:** Porta `5432`
*   **RabbitMQ:** Porta `5672` (Management UI: `http://localhost:15672` - guest/guest)

---

## 🧪 Estratégia de Testes

O projeto adota uma pirâmide de testes rigorosa para garantir a confiabilidade:

### 1. Testes Unitários
Testam a lógica de negócio isolada, parsers de HTML e validações Pydantic.
```bash
# Se tiver ambiente local configurado (ou via Nix)
pytest tests/unit
```

### 2. Testes de Integração (Testcontainers)
Utilizam a biblioteca `Testcontainers` para subir instâncias reais de **PostgreSQL** e **RabbitMQ** em containers efêmeros durante os testes, validando a comunicação real entre os componentes.
```bash
pytest tests/integration
```

---


## 📂 Estrutura do Projeto

```text
├── .github/workflows/  # Pipeline de CI/CD (Lint, Test, Build, Push GCR)
├── alembic/            # Migrações de Banco de Dados
├── app/
│   ├── api/            # Endpoints FastAPI e Healthchecks
│   ├── core/           # Configurações, Logging JSON e RabbitMQ Manager
│   ├── db/             # Conexão SQLAlchemy
│   ├── models/         # Modelos ORM (Job, HockeyData, OscarData)
│   ├── schemas/        # Validação Pydantic (Fail-Fast)
│   ├── scrapers/       # Motores de Scraping (BS4 e Selenium)
│   ├── services/       # Orquestração de Jobs e Idempotência
│   └── worker/         # Consumidor de fila com suporte a DLQ
├── tests/
│   ├── unit/           # Testes unitários (Parsers e Lógica)
│   └── integration/    # Testes com Testcontainers (DB e RabbitMQ)
├── Dockerfile          # Imagem otimizada (Python 3.13 + Chromium)
├── docker-compose.yml  # Orquestração (Healthchecks e Migrations)
└── pyproject.toml      # Dependências e Ferramentas (Ruff, Black)
```

---

## 🌐 Endpoints da API

*   `POST /crawl/hockey`: Inicia coleta de times de Hockey.
*   `POST /crawl/oscar`: Inicia coleta de filmes do Oscar (Selenium).
*   `POST /crawl/all`: Inicia ambas as coletas simultaneamente.
*   `GET /jobs`: Lista todos os jobs e seus status atuais.
*   `GET /jobs/{job_id}/results`: Retorna os dados coletados por um job específico.
*   `GET /results/hockey`: Retorna a base consolidada de times de Hockey.
*   `GET /results/oscar`: Retorna a base consolidada de filmes do Oscar.
