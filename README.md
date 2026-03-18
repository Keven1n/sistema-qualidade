# Sistema de Qualidade — Controle de Soldagem

Sistema web para registro e controle de inspeções de soldagem em linha de produção industrial. Desenvolvido com foco em segurança, rastreabilidade e facilidade de uso no chão de fábrica.

---

## Funcionalidades

- **Autenticação segura** com bcrypt, bloqueio por tentativas e timeout de sessão
- **Dashboard** com indicadores de aprovação, retrabalho e gráficos por soldador e modelo
- **Registro de inspeções** com seleção de modelo, processo, defeitos e upload de fotos
- **Histórico paginado** com filtros por status, soldador e processo
- **Exportação** dos dados em CSV
- **Gerenciamento de usuários** com ativação e desativação de contas
- **Modo demonstração** (visitante) para acesso somente leitura
- **Criptografia opcional** das observações com Fernet

---

## Tecnologias

| Camada | Tecnologia |
|---|---|
| Backend | Python 3.12, FastAPI, Uvicorn |
| Frontend | Jinja2, HTML/CSS |
| Banco de dados | SQLite |
| Autenticação | bcrypt, itsdangerous |
| Criptografia | cryptography (Fernet) |
| Containerização | Docker, Docker Compose |

---
<img width="1919" height="962" alt="image" src="https://github.com/user-attachments/assets/486302ee-e28c-4e7b-a8f9-4ba0aa676e8b" />
<img width="1919" height="956" alt="image" src="https://github.com/user-attachments/assets/7615164e-68c4-4779-9210-ce2b20528aa2" />
<img width="1919" height="955" alt="image" src="https://github.com/user-attachments/assets/e7f576a6-792f-43af-858a-ede3eb840688" />
<img width="1919" height="954" alt="image" src="https://github.com/user-attachments/assets/d677c2e2-601c-44e4-aedd-574d0e3c5b28" />
<img width="1919" height="958" alt="image" src="https://github.com/user-attachments/assets/5ce807a3-2c56-4950-8543-c892a6547bb4" />


## Como rodar localmente

**Pré-requisitos:** Docker e Docker Compose instalados.

```bash
# 1. Clone o repositório
git clone https://github.com/Keven1n/sistema-qualidade.git
cd sistema-qualidade

# 2. Configure as variáveis de ambiente
cp .env
# Edite o .env com sua SECRET_KEY e gere o HASH da senha

# 3. Suba o container
docker-compose up -d
```

Acesse em `http://localhost:8080`

### Gerar hash da senha
```bash
python3 -c "import bcrypt; print(bcrypt.hashpw('SUA_SENHA'.encode(), bcrypt.gensalt()).decode())"
```

---

## Estrutura do projeto

```
sistema-qualidade/
├── app/
│   └── main.py          # Rotas, lógica de negócio e autenticação
├── templates/            # HTML com Jinja2
│   ├── base.html
│   ├── login.html
│   ├── dashboard.html
│   ├── nova.html
│   ├── historico.html
│   ├── editar.html
│   └── usuarios.html
├── static/css/           # Estilos
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

---

## Deploy em produção (VPS)

```bash
# No servidor
apt update && apt install -y docker.io docker-compose
scp -r ./sistema-qualidade usuario@seu-servidor:/opt/sistema-qualidade

cd /opt/sistema-qualidade
cp .env.example .env
nano .env

docker-compose up -d
```

Recomendado colocar Nginx na frente com HTTPS via Let's Encrypt.

---

## Segurança

- Senhas armazenadas com hash bcrypt
- Sessões assinadas com chave secreta (itsdangerous)
- Bloqueio de conta após tentativas excessivas de login
- Timeout automático de sessão por inatividade
- Validação de tipo de arquivo por magic bytes (não apenas extensão)
- Observações criptografadas com Fernet (opcional)
- Proteção contra path traversal no upload de imagens

---

## Comandos úteis

```bash
# Logs em tempo real
docker-compose logs -f

# Reconstruir após mudanças no código
docker-compose up -d --build

# Parar
docker-compose down
```
