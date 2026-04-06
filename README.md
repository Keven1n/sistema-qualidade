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

<img width="1920" height="998" alt="image" src="https://github.com/user-attachments/assets/805d1333-56ce-49b4-bd98-0a0bbc45c5aa" />

**Dashboard**

Painel analítico com KPIs, gráficos interativos e exportação de dossiê em PDF.

<img width="1920" height="998" alt="image" src="https://github.com/user-attachments/assets/8fb0a52d-86a7-48b6-8fec-ac7780da9463" />

**Nova Inspeção**

Formulário com seleção de linha/modelo, leitor de QR Code, upload de fotos e assinatura digital.

<img width="1920" height="998" alt="image" src="https://github.com/user-attachments/assets/47ed8975-578e-40cd-829b-c27ae79f42c7" />

**Histórico de Inspeções**

Registros com filtros avançados, geração de laudos PDF e reinspeção vinculada.

<img width="1920" height="998" alt="image" src="https://github.com/user-attachments/assets/b9daade2-551e-4a95-97be-2d8e2ee6cf83" />

**Gestão de Usuários**

Ativação/desativação de contas e criação de novos usuários com níveis de permissão.

<img width="1920" height="998" alt="image" src="https://github.com/user-attachments/assets/6e7b7d8e-8c35-4d81-aaa3-41d52fe87c12" />

**Auditoria**

Registro cronológico de todas as ações realizadas no sistema (login, logout, criação de inspeções, alterações de cadastro). Permite filtrar por usuário e tipo de ação, com exportação completa em CSV para conformidade e rastreabilidade.

<img width="1920" height="998" alt="image" src="https://github.com/user-attachments/assets/65994231-ace7-49c1-82dc-71becd9fe45a" />

**Soldadores**

Cadastro e gerenciamento dos soldadores da fábrica. Centraliza os nomes dos profissionais que aparecem nos formulários de inspeção, garantindo padronização e evitando duplicidades no registro das O.S.

<img width="1920" height="998" alt="image" src="https://github.com/user-attachments/assets/ccd709c9-7cda-4cce-aedc-c3db16b2e530" />

**Catálogo de Modelos**

Administração das linhas de produção e seus respectivos modelos de tanques. Define quais equipamentos estão disponíveis para seleção no formulário de nova inspeção, mantendo o catálogo sempre atualizado com a realidade da fábrica.

<img width="1920" height="998" alt="image" src="https://github.com/user-attachments/assets/80254347-c115-48fb-b12e-74dc93ecb4b1" />

---

## Autor

**Kevin** — [github.com/Keven1n](https://github.com/Keven1n) · [linkedin.com/in/kevin-90040agui](https://linkedin.com/in/kevin-90040agui)
