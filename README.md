**Estoque Manutenção**
Sistema de controle de estoque e solicitações de materiais desenvolvido em Django e Tailwind CSS, focado no setor de manutenção. 
Este projeto digitaliza o processo de solicitação de peças, implementando um fluxo de trabalho com aprovação gerencial, controle de inventário em tempo real e relatórios de gastos.

**Contexto do Projeto**
Este sistema foi desenvolvido para resolver a necessidade de um controle de inventário digitalizado para o setor de manutenção. 
O processo anterior, manual, dificultava a rastreabilidade de peças, gerava contagens de estoque imprecisas e não oferecia uma visão clara dos custos de material.
A plataforma "Estoque Manutenção" centraliza o inventário, formaliza o fluxo de solicitações através de um sistema de aprovação e fornece dados em tempo real para a gestão.

**Funcionalidades Principais**

Controle de Acesso por Nível: O sistema diferencia usuários Normais (que podem solicitar itens) de Supervisores (que gerenciam o estoque e aprovam solicitações).

Gestão de Inventário (CRUD): Supervisores podem criar, editar e visualizar todos os itens do estoque, incluindo nome, código, categoria, valor, localização e imagem.

Fluxo de Retirada com Carrinho: Usuários podem navegar pelo estoque, adicionar múltiplos itens a um carrinho, ajustar quantidades e submeter uma solicitação formal de retirada.

Sistema de Aprovação: As solicitações ficam com status "Pendente" até que um supervisor as aprove (debitando o estoque) ou recuse (informando um motivo).

Página de Histórico: Um registro completo de todas as retiradas, com visualizações diferentes para usuários (veem apenas seus pedidos) e supervisores (veem todos os pedidos).

Dashboard Gerencial: Uma página de análise visual para supervisores com um gráfico de barras dos gastos totais por semana.

Notificações em Tempo Real (AJAX Polling): A página de histórico do supervisor se atualiza automaticamente quando novas solicitações chegam, e o usuário é notificado em tempo real quando seu pedido é aprovado/recusado.

Design Responsivo: A interface é 100% funcional e otimizada para uso em dispositivos móveis, incluindo um menu "hamburger" e um carrinho "sanfona".

**Tecnologias Utilizadas**
Backend:

Python 3.13

Django 5.2 (para toda a lógica de backend, views e ORM)

Django Channels (para a infraestrutura de tempo real)

Frontend:

HTML5

Tailwind CSS 3 (para todo o design e layout responsivo)

JavaScript (ES6+) (para interatividade do carrinho, modals e chamadas de API)

Chart.js (para a renderização dos gráficos no dashboard)

Banco de Dados:

SQLite3 (para desenvolvimento e produção simplificada)

Deployment:

PythonAnywhere (Hospagem)

Gunicorn / Daphne (Servidor de aplicação ASGI/WSGI)


**Como Rodar o Projeto Localmente**
Para rodar este projeto no seu computador, siga os passos abaixo.

1. Pré-requisitos
    Python 3.10+

    Node.js e npm (necessários para o Tailwind CSS)

2. Clonar o Repositório
Bash

git clone https://github.com/seu-usuario/seu-repositorio.git
cd seu-repositorio
3. Configurar o Ambiente Python
Bash

python -m venv venv

# No Windows:
.\venv\Scripts\activate
# No macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
4. Configurar o Ambiente Frontend (Tailwind)
Bash

npm install

**5. Configurar o Banco de Dados**
Bash

python manage.py migrate

# Crie um superusuário para acessar o Admin
python manage.py createsuperuser

**6. Rodar os Servidores**
Você precisará de dois terminais abertos ao mesmo tempo.

No Terminal 1 (Servidor de Build do Tailwind): Este comando "vigia" seus arquivos HTML e reconstrói o styles.css automaticamente sempre que você faz uma alteração no layout.

Bash

npx tailwindcss -i ./src/input.css -o ./app_estoque/static/css/styles.css --watch
No Terminal 2 (Servidor do Django): Este comando inicia o servidor de desenvolvimento do Django (já configurado com Daphne para tempo real).

Bash

python manage.py runserver
