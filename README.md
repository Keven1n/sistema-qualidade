# ThermoLac — Quality Control Platform

![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?style=flat&logo=fastapi&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-ready-2496ED?style=flat&logo=docker&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-database-4169E1?style=flat&logo=postgresql&logoColor=white)
![PWA](https://img.shields.io/badge/PWA-installable-5A0FC8?style=flat&logo=pwa&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-green?style=flat)

---

## Sobre o Projeto

Plataforma web completa para registro e controle de inspeções de soldagem em linhas de produção industrial. Desenvolvida como Progressive Web App (PWA), funciona diretamente no celular do inspetor sem necessidade de instalação via loja de apps.

O sistema oferece rastreabilidade total do processo de qualidade: desde o registro fotográfico no chão de fábrica até a emissão de laudos técnicos em PDF com assinatura digital eletrônica.

---

## Funcionalidades

### Dashboard Analítico
- Indicadores visuais (KPIs): total de inspeções, aprovações, reprovações e taxa de aprovação
- Gráficos interativos com Chart.js: distribuição por status, soldador, modelo e defeitos
- Filtro por período (data inicial e final)
- Exportação de dossiê gerencial consolidado em PDF com os gráficos do período

### Registro de Inspeções
- Seleção de linha de produção, modelo de tanque, soldador e processo (TIG Manual/Orbital)
- Marcação de defeitos encontrados via checkboxes
- Upload de múltiplas fotos como evidência fotográfica
- Leitor de QR Code integrado via câmera do celular para preenchimento automático do número da O.S.
- Assinatura digital eletrônica desenhada diretamente na tela (Canvas)
- Pré-preenchimento automático para reinspeções de peças reprovadas

### Histórico de Inspeções
- Listagem completa com filtros por status, soldador, processo e período
- Geração de laudo técnico individual em PDF (com cabeçalho, dados, defeitos, fotos e assinatura)
- Botão de reinspeção que herda dados do registro original
- Exportação do histórico filtrado em CSV

### Gestão Administrativa (Admin)
- **Usuários:** cadastro, ativação/desativação de contas e definição de papéis (admin/inspetor)
- **Soldadores:** cadastro e gerenciamento dos soldadores da fábrica
- **Catálogo:** administração das linhas de produção e modelos de tanques
- **Auditoria:** log completo de todas as ações realizadas no sistema com exportação em CSV

### Progressive Web App (PWA)
- Instalável na tela inicial de celulares Android e iOS
- Navegação mobile via Bottom Tab-Bar com ícones SVG e botão flutuante central
- Interface responsiva que converte tabelas em cartões empilhados em telas pequenas
- Viewport travado para impedir zoom e arraste lateral acidental

### Dark Mode
- Alternância entre tema claro e escuro com persistência via localStorage
- Prevenção de flash branco (FOUC) com script de inicialização no cabeçalho
- Todas as cores, bordas e sombras adaptadas automaticamente

### Geração de PDFs
- **Laudo Técnico:** documento formal por inspeção com dados do equipamento, defeitos, evidências fotográficas em alta resolução e assinatura eletrônica do inspetor
- **Dossiê Gerencial:** relatório consolidado do período com KPIs e gráficos capturados diretamente do dashboard (conversão Canvas → Base64 → PDF)

### Segurança
- Senhas criptografadas com bcrypt
- Sessões assinadas com chave secreta (itsdangerous) e timeout automático
- Limitação de tentativas de login e bloqueio de conta
- Validação de uploads por magic bytes (não apenas extensão do arquivo)
- Criptografia opcional de observações com Fernet
- Proteção contra path traversal em uploads de imagens
- Logs de auditoria para rastreamento de ações sensíveis

### Backup Automatizado
- Script de backup diário do banco de dados PostgreSQL
- Compactação automática das evidências fotográficas em ZIP
- Rotatividade de 7 dias (backups antigos são removidos automaticamente)
- Script shell auxiliar para execução manual

---

## Tecnologias

| Camada | Tecnologia |
|---|---|
| Backend | Python 3.12, FastAPI, Uvicorn |
| Frontend | Jinja2, HTML5, CSS3, JavaScript |
| Gráficos | Chart.js |
| Banco de dados | PostgreSQL |
| Geração de PDF | WeasyPrint |
| Autenticação | bcrypt, itsdangerous |
| Criptografia | cryptography (Fernet) |
| QR Code | html5-qrcode |
| Containerização | Docker, Docker Compose |
| Proxy reverso | Nginx (HTTPS) |

---

## Screenshots

**Login**

Tela segura de autenticação com modo demonstração (visitante) para acesso somente leitura.

<img width="1919" height="956" alt="Login" src="https://github.com/user-attachments/assets/af9217f3-c67f-463b-83e2-82fd601f291d" />

**Dashboard**

Painel analítico com KPIs, gráficos interativos e exportação de dossiê em PDF.

<img width="1918" height="957" alt="Dashboard" src="https://github.com/user-attachments/assets/acc47766-55b8-4a39-807c-71451abbc641" />

**Nova Inspeção**

Formulário com seleção de linha/modelo, leitor de QR Code, upload de fotos e assinatura digital.

<img width="1917" height="955" alt="Nova Inspeção" src="https://github.com/user-attachments/assets/d76d3029-c09f-4ebc-976b-e7f928ad015a" />

**Histórico de Inspeções**

Registros com filtros avançados, geração de laudos PDF e reinspeção vinculada.

<img width="1917" height="949" alt="Historico Inspeções" src="https://github.com/user-attachments/assets/92ba645d-4699-43ed-bdad-b5ccad353d15" />

**Gestão de Usuários**

Ativação/desativação de contas e criação de novos usuários com níveis de permissão.

<img width="1919" height="959" alt="Area de Usuarios" src="https://github.com/user-attachments/assets/b67cac6d-638e-4388-a1a3-16ec11d286b5" />

---

## Autor

**Kevin** — [github.com/Keven1n](https://github.com/Keven1n) · [linkedin.com/in/kevin-90040agui](https://linkedin.com/in/kevin-90040agui)
