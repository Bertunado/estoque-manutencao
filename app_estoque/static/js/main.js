document.addEventListener('DOMContentLoaded', () => {

    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    const csrftoken = getCookie('csrftoken');

    const menuBtn = document.getElementById('menu-btn');
    const sidebar = document.getElementById('sidebar');
    if (menuBtn && sidebar) {
        menuBtn.addEventListener('click', () => {
            sidebar.classList.toggle('-translate-x-full');
        });
    }

    // LÓGICA DA PÁGINA DE RETIRADA
    const isRetiradaPage = document.getElementById('carrinho-container'); // Verificação mais segura
    if (isRetiradaPage) {

        const itensDisponiveis = {};
        document.querySelectorAll('.item-card').forEach(card => {
            const button = card.querySelector('.btn-adicionar');
            if (button) {
                const itemId = button.dataset.itemId;
                itensDisponiveis[itemId] = {
                    id: itemId,
                    nome: card.querySelector('[data-name]').textContent,
                    codigo: card.querySelector('[data-code]').textContent.replace('Código: ', ''),
                    valor: parseFloat(card.querySelector('[data-valor]').dataset.valor),
                    imagem_url: card.querySelector('img').src,
                };
            }
        });

        let carrinho = {};

        const ui = {
            desktop: {
                container: document.getElementById('carrinho-container'),
                vazio: document.getElementById('carrinho-vazio'),
                contador: document.getElementById('contador-carrinho'),
                total: document.getElementById('carrinho-total'),
                limparBtn: document.getElementById('limpar-carrinho-btn'),
            },
            mobile: {
                container: document.getElementById('carrinho-container-mobile'),
                vazio: document.getElementById('carrinho-vazio-mobile'),
                contador: document.getElementById('contador-carrinho-mobile'),
                total: document.getElementById('carrinho-total-mobile'),
                limparBtn: document.getElementById('limpar-carrinho-btn-mobile'),
            },
            template: document.getElementById('carrinho-item-template'),
            popup: document.getElementById('item-adicionado-popup'),
            fecharPopupBtn: document.getElementById('fechar-popup-btn'),
        };

        function renderizarCarrinho() {
            const carrinhoArray = Object.values(carrinho);
            let valorTotal = 0;

            if (ui.desktop.container) ui.desktop.container.innerHTML = '';
            if (ui.mobile.container) ui.mobile.container.innerHTML = '';

            if (carrinhoArray.length === 0) {
                if (ui.desktop.container && ui.desktop.vazio) ui.desktop.container.appendChild(ui.desktop.vazio);
                if (ui.mobile.container && ui.mobile.vazio) ui.mobile.container.appendChild(ui.mobile.vazio);
            } else {
                carrinhoArray.forEach(item => {
                    valorTotal += item.valor * item.quantidade;
                    [ui.desktop.container, ui.mobile.container].forEach(container => {
                        if (container) {
                            const clone = ui.template.content.cloneNode(true);
                            const itemDiv = clone.querySelector('.carrinho-item');
                            itemDiv.dataset.itemId = item.id;
                            clone.querySelector('img').src = item.imagem_url;
                            clone.querySelector('h4').textContent = item.nome;
                            clone.querySelector('p').textContent = `Código: ${item.codigo}`;
                            clone.querySelector('select').value = item.quantidade;
                            container.appendChild(clone);
                        }
                    });
                });
            }

            const totalFormatado = `R$ ${valorTotal.toFixed(2).replace('.', ',')}`;
            const numItens = carrinhoArray.length;
            if (ui.desktop.contador) ui.desktop.contador.textContent = numItens;
            if (ui.mobile.contador) ui.mobile.contador.textContent = numItens;
            if (ui.desktop.total) ui.desktop.total.textContent = totalFormatado;
            if (ui.mobile.total) ui.mobile.total.textContent = totalFormatado;
        }

        function atualizarSessao(url, method, body) {
            fetch(url, {
                method: method,
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrftoken },
                body: body ? JSON.stringify(body) : null,
            })
            .then(res => res.json())
            .then(data => console.log(data.message))
            .catch(err => console.error('Erro de comunicação com o servidor:', err));
        }

        document.querySelectorAll('.btn-adicionar').forEach(button => {
            button.addEventListener('click', () => {
                const itemId = button.dataset.itemId;
                if (!carrinho[itemId]) {
                    carrinho[itemId] = { ...itensDisponiveis[itemId], quantidade: 1 };
                    renderizarCarrinho();
                    atualizarSessao(`/carrinho/adicionar/${itemId}/`, 'POST');
                }
                if (ui.popup) {
                    ui.popup.classList.remove('hidden');
                    ui.popup.classList.add('flex');
                }
            });
        });

        if (ui.fecharPopupBtn) {
            ui.fecharPopupBtn.addEventListener('click', () => {
                ui.popup.classList.add('hidden');
                ui.popup.classList.remove('flex');
            });
        }

        [ui.desktop.limparBtn, ui.mobile.limparBtn].forEach(btn => {
            if (btn) {
                btn.addEventListener('click', () => {
                    const url = btn.dataset.limparUrl;
                    carrinho = {};
                    renderizarCarrinho();
                    atualizarSessao(url, 'POST');
                });
            }
        });

        document.body.addEventListener('click', event => {
            if (event.target.closest('.btn-remover')) {
                const itemDiv = event.target.closest('.carrinho-item');
                if (itemDiv) {
                    const itemId = itemDiv.dataset.itemId;
                    delete carrinho[itemId];
                    renderizarCarrinho();
                }
            }
        });

        document.body.addEventListener('change', event => {
            const select = event.target.closest('.carrinho-item select');
            if (select) {
                const itemDiv = select.closest('.carrinho-item');
                const itemId = itemDiv.dataset.itemId;
                const novaQuantidade = parseInt(select.value);

                if (carrinho[itemId]) {
                    carrinho[itemId].quantidade = novaQuantidade;
                    renderizarCarrinho();
                    const url = ui.desktop.container.dataset.updateUrl;
                    atualizarSessao(url, 'POST', { 'item_id': itemId, 'quantidade': novaQuantidade });
                }
            }
        });
    }

    // LÓGICA DA PÁGINA DE HISTÓRICO
    const historicoContainer = document.querySelector('.space-y-6');
    if (historicoContainer) {

        // Lógica do Modal de Recusa
        const modal = document.getElementById('recusar-modal');
        if (modal) {
            const modalForm = document.getElementById('recusar-form');
            const cancelarBtn = document.getElementById('cancelar-recusa-btn');
            const botoesRecusar = document.querySelectorAll('.btn-recusar');

            botoesRecusar.forEach(button => {
                button.addEventListener('click', () => {
                    const retiradaId = button.dataset.retiradaId;
                    modalForm.action = `/retirada/${retiradaId}/recusar/`; // URL ajustada para o padrão do Django
                    modal.classList.remove('hidden');
                    modal.classList.add('flex');
                });
            });
            cancelarBtn.addEventListener('click', () => {
                modal.classList.add('hidden');
                modal.classList.remove('flex');
            });
            modal.addEventListener('click', (event) => {
                if (event.target === modal) {
                    modal.classList.add('hidden');
                    modal.classList.remove('flex');
                }
            });
        }

        // ATUALIZAÇÃO EM TEMPO REAL
        // Substitui o WebSocket problemático por uma checagem a cada 7 segundos
        const agoraEmFormatoISO = new Date().toISOString();

        setInterval(() => {
            fetch(`/notificacoes/verificar/?since=${agoraEmFormatoISO}`) // URL corrigida para o seu urls.py
                .then(response => response.json())
                .then(data => {
                    if (data.novas_retiradas) {
                        console.log("Novas retiradas encontradas! Recarregando...");

                        const alertBox = document.createElement('div');
                        alertBox.className = 'fixed top-5 right-5 bg-green-500 text-white py-2 px-4 rounded-lg shadow-lg z-50 transition-opacity duration-500';
                        alertBox.textContent = 'Nova retirada solicitada! Atualizando...';
                        document.body.appendChild(alertBox);

                        setTimeout(() => {
                            location.reload();
                        }, 1500);
                    }
                })
                .catch(err => console.log("Erro no polling:", err));
        }, 7000);
    }

    // SISTEMA DE NOTIFICAÇÕES NA NAVBAR
    const notificacoesBtn = document.getElementById('notificacoes-btn');
    if (notificacoesBtn) {
        const notificacoesPanel = document.getElementById('notificacoes-panel');
        const notificacoesLista = document.getElementById('notificacoes-lista');
        const notificacaoBadge = document.getElementById('notificacao-badge');
        const notificacaoTemplate = document.getElementById('notificacao-template');
        const urlMarcarLido = notificacoesBtn.dataset.urlMarcarLido;
        const csrfTokenNotificacao = notificacoesBtn.dataset.csrfToken;

        const unreadDataElement = document.getElementById('unread-notifications-data');
        let unreadNotifications = unreadDataElement ? JSON.parse(unreadDataElement.textContent) : [];

        notificacoesBtn.addEventListener('click', () => {
            notificacoesPanel.classList.toggle('hidden');
            if (!notificacoesPanel.classList.contains('hidden') && unreadNotifications.length > 0) {
                notificacoesLista.innerHTML = '';
                unreadNotifications.forEach(notif => {
                    const clone = notificacaoTemplate.content.cloneNode(true);
                    clone.querySelector('.notification-message').textContent = notif.mensagem;
                    const dataFormatada = new Date(notif.data_criacao).toLocaleString('pt-BR');
                    clone.querySelector('.notification-date').textContent = dataFormatada;

                    if (notif.details) {
                        const detailsContainer = clone.querySelector('.notification-details');
                        const itemList = clone.querySelector('.notification-item-list');
                        const reasonContainer = clone.querySelector('.notification-reason');
                        const reasonText = clone.querySelector('.notification-reason-text');

                        notif.details.itens.forEach(itemText => {
                            const li = document.createElement('li');
                            li.textContent = itemText;
                            itemList.appendChild(li);
                        });
                        reasonText.textContent = notif.details.motivo;

                        detailsContainer.classList.remove('hidden');
                        reasonContainer.classList.remove('hidden');
                    }

                    notificacoesLista.appendChild(clone);
                });

                if (notificacaoBadge) {
                    notificacaoBadge.remove();
                }

                fetch(urlMarcarLido, {
                    method: 'POST',
                    headers: { 'X-CSRFToken': csrfTokenNotificacao, 'Content-Type': 'application/json' },
                })
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'success') {
                        console.log('Notificações marcadas como lidas.');
                        unreadNotifications.length = 0; // Limpa o array local
                    }
                });
            }
        });
    }
});