# Sistema de Qualidade — Welding Quality Control System

![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?style=flat&logo=fastapi&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-ready-2496ED?style=flat&logo=docker&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-database-003B57?style=flat&logo=sqlite&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-green?style=flat)

---

## Português

Sistema web para registro e controle de inspeções de soldagem em linha de produção industrial. Desenvolvido com foco em segurança, rastreabilidade e facilidade de uso no chão de fábrica.

### Funcionalidades

- **Dashboard** com indicadores de aprovação, retrabalho e gráficos por soldador e modelo
- **Registro de inspeções** com seleção de modelo, processo, defeitos e upload de fotos
- **Histórico paginado** com filtros por status, soldador e processo
- **Exportação** dos dados em CSV
- **Autenticação segura** com bcrypt, bloqueio por tentativas e timeout de sessão
- **Gerenciamento de usuários** com ativação e desativação de contas
- **Modo demonstração** (visitante) para acesso somente leitura
- **Criptografia opcional** das observações com Fernet

### Tecnologias

| Camada | Tecnologia |
|---|---|
| Backend | Python 3.12, FastAPI, Uvicorn |
| Frontend | Jinja2, HTML/CSS |
| Banco de dados | SQLite |
| Autenticação | bcrypt, itsdangerous |
| Criptografia | cryptography (Fernet) |
| Containerização | Docker, Docker Compose |

---

## English

A full-stack web application built to support welding inspection and quality control in industrial production lines. The system allows teams to register inspections, track defects, manage rework, and export reports — with a focus on traceability and ease of use on the factory floor.

### Features

- **Dashboard** with real-time approval and rework metrics, charts by welder and model
- **Inspection registration** with model/process selection, defect tagging, and photo upload
- **Paginated history** with filters by status, welder, and process
- **CSV export** of inspection data
- **Secure authentication** with bcrypt, login attempt throttling, and session timeout
- **User management** with account activation and deactivation
- **Demo mode** (guest access) for read-only browsing
- **Optional encryption** of observations using Fernet

### Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.12, FastAPI, Uvicorn |
| Frontend | Jinja2, HTML/CSS |
| Database | SQLite |
| Authentication | bcrypt, itsdangerous |
| Encryption | cryptography (Fernet) |
| Containerization | Docker, Docker Compose |

---

## Getting Started / Como rodar

**Prerequisites / Pré-requisitos:** Docker and Docker Compose installed.

```bash
# 1. Clone the repository
git clone https://github.com/Keven1n/sistema-qualidade.git
cd sistema-qualidade

# 2. Set up environment variables
cp .env.example .env
# Edit .env with your SECRET_KEY and password hash

# 3. Start the container
docker-compose up -d
```

Access at / Acesse em: `http://localhost:8080`

### Generate password hash / Gerar hash da senha

```bash
python3 -c "import bcrypt; print(bcrypt.hashpw('YOUR_PASSWORD'.encode(), bcrypt.gensalt()).decode())"
```

---

## Security / Segurança

- Passwords hashed with **bcrypt**
- Sessions signed with secret key (**itsdangerous**) and automatic timeout
- Login attempt **rate limiting** and account lockout
- File upload validated by **magic bytes** (not just extension)
- Observations optionally **encrypted with Fernet**
- Protection against **path traversal** in image uploads

---

## Project Structure / Estrutura do projeto

```
sistema-qualidade/
├── app/
│   └── main.py           # Routes, business logic, authentication
├── templates/             # HTML with Jinja2
│   ├── base.html
│   ├── login.html
│   ├── dashboard.html
│   ├── nova.html
│   ├── historico.html
│   ├── editar.html
│   └── usuarios.html
├── static/css/            # Stylesheets
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

---

## Production Deploy

```bash
# On your server
apt update && apt install -y docker.io docker-compose
scp -r ./sistema-qualidade user@your-server:/opt/sistema-qualidade

cd /opt/sistema-qualidade
cp .env.example .env
nano .env

docker-compose up -d
```

> Recommended: place Nginx in front with HTTPS via Let's Encrypt.

---

## Useful Commands / Comandos úteis

```bash
# Live logs
docker-compose logs -f

# Rebuild after code changes
docker-compose up -d --build

# Stop
docker-compose down
```

---

## Author / Autor

**Kevin** — [github.com/Keven1n](https://github.com/Keven1n) · [linkedin.com/in/kevin-90040agui](https://linkedin.com/in/kevin-90040agui)
