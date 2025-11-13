# Copilot Instructions for estoque_geral

## Visão Geral
Este projeto é uma aplicação Django para gestão de estoque, com frontend customizado usando Tailwind CSS e JavaScript. O fluxo principal envolve cadastro, visualização e retirada de itens do estoque.

## Estrutura Principal
- `app_estoque/`: App Django principal, contém modelos, views, urls e templates.
- `app_estoque/static/`: Arquivos estáticos (CSS, JS). O JS (`main.js`) gerencia o carrinho de retirada de itens.
- `app_estoque/templates/`: Templates HTML, como `retirada_itens.html`.
- `settings.py`, `urls.py`: Configuração global do Django.
- `media/`: Armazenamento de imagens dos itens.

## Padrões e Convenções
- **Carrinho de Retirada:** O frontend usa delegação de eventos para manipular o carrinho. Adições/remover itens são feitas via POST para endpoints Django, usando CSRF token.
- **Templates:** O HTML usa classes Tailwind e templates Django (`{% ... %}`) para renderização dinâmica.
- **Imagens:** Itens têm imagens associadas, salvas em `media/itens/`.
- **Migrations:** Alterações de modelo devem ser migradas com `python manage.py makemigrations` e `python manage.py migrate`.

## Fluxos de Desenvolvimento
- **Rodar o servidor:**
  ```powershell
  python manage.py runserver
  ```
- **Criar/Aplicar migrations:**
  ```powershell
  python manage.py makemigrations
  python manage.py migrate
  ```
- **Coletar arquivos estáticos:**
  ```powershell
  python manage.py collectstatic
  ```
- **Debug:** Use o console do navegador para JS e o terminal para logs Django.

## Integrações e Dependências
- **Tailwind CSS:** Configurado via `tailwind.config.js` e `src/input.css`.
- **Django:** Backend principal, banco SQLite (`db.sqlite3`).
- **JavaScript:** Manipula o carrinho e interage com endpoints Django.

## Exemplos de Padrões
- **Adição ao carrinho:**
  - JS faz POST para `/carrinho/adicionar/<item_id>/`.
  - Backend deve responder com JSON `{ status: 'success', ... }`.
- **Remoção do carrinho:**
  - JS remove elemento do DOM e atualiza contador.

## Recomendações para Agentes
- Mantenha a compatibilidade com Django e Tailwind.
- Siga o padrão de manipulação do carrinho em `main.js`.
- Use templates e rotas existentes para novas funcionalidades.
- Atualize migrations ao alterar modelos.

## Arquivos-chave
- `app_estoque/models.py`, `views.py`, `urls.py`
- `app_estoque/static/js/main.js`
- `app_estoque/templates/retirada_itens.html`
- `settings.py`, `urls.py`, `tailwind.config.js`

---

Seções incompletas ou dúvidas? Solicite exemplos ou esclarecimentos sobre fluxos específicos.