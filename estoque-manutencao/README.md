**Estoque Manutenção**

Sistema de controle de estoque e solicitações de materiais desenvolvido em Django e Tailwind CSS, focado no setor de manutenção. 
Este projeto digitaliza o processo de solicitação de peças, implementando um fluxo de trabalho com aprovação gerencial, controle de inventário em tempo real e relatórios de gastos.

**Contexto do Projeto**

Este sistema foi desenvolvido para resolver a necessidade de um controle de inventário digitalizado para o setor de manutenção. 
O processo anterior, manual, dificultava a rastreabilidade de peças, gerava contagens de estoque imprecisas e não oferecia uma visão clara dos custos de material.
A plataforma "Estoque Manutenção" centraliza o inventário, formaliza o fluxo de solicitações através de um sistema de aprovação e fornece dados em tempo real para a gestão.

* **Funcionalidades Principais**

  * Controle de Acesso por Nível: O sistema diferencia usuários Normais (que podem solicitar itens) de Supervisores (que gerenciam o estoque e aprovam solicitações).

  * Gestão de Inventário (CRUD): Supervisores podem criar, editar e visualizar todos os itens do estoque, incluindo nome, código, categoria, valor, localização e imagem.

  * Fluxo de Retirada com Carrinho: Usuários podem navegar pelo estoque, adicionar múltiplos itens a um carrinho, ajustar quantidades e submeter uma solicitação formal de retirada.

  * Sistema de Aprovação: As solicitações ficam com status "Pendente" até que um supervisor as aprove (debitando o estoque) ou recuse (informando um motivo).

  * Página de Histórico: Um registro completo de todas as retiradas, com visualizações diferentes para usuários (veem apenas seus pedidos) e supervisores (veem todos os pedidos).

  * Dashboard Gerencial: Uma página de análise visual para supervisores com um gráfico de barras dos gastos totais por semana.

  * Notificações em Tempo Real (AJAX Polling): A página de histórico do supervisor se atualiza automaticamente quando novas solicitações chegam, e o usuário é notificado em tempo real quando seu pedido é aprovado/recusado.

  * Design Responsivo: A interface é 100% funcional e otimizada para uso em dispositivos móveis, incluindo um menu "hamburger" e um carrinho "sanfona".

* **Tecnologias Utilizadas**
  
  * Backend:

  * Python 3.13

  * Django 5.2 (para toda a lógica de backend, views e ORM)

  * Django Channels (para a infraestrutura de tempo real)

* **Frontend:**

  * HTML5

  * Tailwind CSS 3 (para todo o design e layout responsivo)

  * JavaScript (ES6+) (para interatividade do carrinho, modals e chamadas de API)

  * Chart.js (para a renderização dos gráficos no dashboard)
    

* **Banco de Dados:**

  * SQLite3 (para desenvolvimento e produção simplificada)
    

* **Deployment:**

  * PythonAnywhere (Hospagem)

  * Gunicorn / Daphne (Servidor de aplicação ASGI/WSGI)

