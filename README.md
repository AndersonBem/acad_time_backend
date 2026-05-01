# 🎓 AcadTime - Backend

Backend do sistema AcadTime, uma API REST desenvolvida em Django para gerenciamento de atividades complementares acadêmicas.

---

## 🚀 Sobre o Projeto

O AcadTime é uma plataforma que permite o controle completo de atividades complementares, incluindo:

- Submissão de atividades por alunos
- Upload e validação de certificados
- Controle de status: pendente, aprovado e rejeitado
- Gestão por coordenadores
- Controle administrativo por SuperAdmin

Este repositório contém o backend da aplicação, responsável pela lógica de negócio, regras, autenticação e persistência de dados.

---

## 🛠️ Tecnologias Utilizadas

- Python
- Django
- Django REST Framework
- PostgreSQL
- JWT
- Swagger / drf-yasg
- AWS S3
- API de envio de e-mails


---

## 🧱 Arquitetura

O projeto utiliza uma API REST separada do frontend, com regras de negócio aplicadas no backend e validações críticas também implementadas no banco de dados.

O banco PostgreSQL utiliza scripts SQL, triggers, functions e procedures para reforçar regras importantes do sistema.

---

## 📂 Estrutura do Projeto

backend/
├── api/
├── banco_completo/
├── config/
├── manage.py
├── requirements.txt
└── requirements-dev.txt

---

## 🔐 Autenticação

A autenticação é feita com JWT.

O token deve ser enviado no header das requisições:

Authorization: Bearer seu_token_aqui

---

## 👤 Perfis de Usuário

O sistema possui três perfis principais:

- Aluno
- Coordenador
- SuperAdmin

Cada perfil possui permissões específicas dentro da API.

---

## 📦 Principais Funcionalidades

- Login com JWT
- Cadastro e gerenciamento de usuários
- Controle de alunos, coordenadores e administradores
- Cadastro de cursos
- Cadastro de tipos de atividade
- Regras de carga horária por curso e tipo de atividade
- Submissão de atividades complementares
- Upload de certificados
- Aprovação e rejeição de submissões
- Controle de inscrições em cursos
- Auditoria de ações
- Notificações por e-mail

---

## 🗄️ Banco de Dados

O banco utilizado é PostgreSQL.

A estrutura do banco é mantida por scripts SQL na pasta:

banco_completo/

O projeto utiliza:

- Tabelas relacionais
- Functions
- Procedures
- Triggers
- Logs de auditoria

---

## ⚙️ Como Executar o Projeto

1. Clone o repositório:

git clone https://github.com/AndersonBem/acad_time_backend.git

2. Acesse a pasta do projeto:

cd acad_time_backend

3. Crie o ambiente virtual:

python -m venv venv

4. Ative o ambiente virtual no Windows:

venv\Scripts\activate

5. Instale as dependências:

pip install -r requirements-dev.txt

6. Configure as variáveis de ambiente em um arquivo .env.

Exemplo:

DEBUG=True  
SECRET_KEY=sua_chave_secreta  
DB_NAME=nome_do_banco  
DB_USER=usuario_do_banco  
DB_PASSWORD=senha_do_banco  
DB_HOST=localhost  
DB_PORT=5432  

7. Execute o servidor:

python manage.py runserver

---

## 🔗 Endpoints Principais

- /login/
- /usuarios/
- /aluno/
- /coordenador/
- /curso/
- /tipo-atividade/
- /regra-atividade/
- /atividade-complementar/
- /submissao/
- /inscricao/
- /auditoria/
- /notificacao-email/

---

## 📊 Documentação da API

A API possui documentação via Swagger.

Acesse:

/swagger/

---

## 🌐 Deploy

O backend pode ser hospedado em:

- Render
- Railway
- VPS
- Docker

---

## 📌 Observações

- Este backend depende de um banco PostgreSQL configurado corretamente.
- O frontend consome esta API.
- As regras principais do sistema são reforçadas tanto no backend quanto no banco de dados.
- Não é recomendado utilizar SQLite em produção.

---

## 👨‍💻 Autores

Desenvolvido por:
- Anderson Alexandre (https://github.com/AndersonBem)
- Wendell Barboza (https://github.com/Wendell8708)
- Laís Nayara (https://github.com/LNayaraSilva)
  
Recife - PE
