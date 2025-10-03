document.addEventListener('DOMContentLoaded', () => {

    const menuBtn = document.getElementById('menu-btn');
    const sidebar = document.getElementById('sidebar');

    if (menuBtn && sidebar) {
        menuBtn.addEventListener('click', () => {
            sidebar.classList.toggle('-translate-x-full');
        });
    }
    

    // Função auxiliar para pegar o CSRF token, necessária em vários blocos
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


    // --- BLOCO 1: LÓGICA DA PÁGINA DE RETIRADA (CARRINHO) ---
    const retiradaContainer = document.getElementById('carrinho-container');
    if (retiradaContainer) {
        
        const popup = document.getElementById('item-adicionado-popup');
        const fecharPopupBtn = document.getElementById('fechar-popup-btn');
        const carrinhoVazioMensagem = document.getElementById('carrinho-vazio');
        const contadorCarrinho = document.getElementById('contador-carrinho');
        const carrinhoTotalEl = document.getElementById('carrinho-total');
        const carrinhoItemTemplate = document.getElementById('carrinho-item-template');
        const botoesAdicionar = document.querySelectorAll('.btn-adicionar');
        const limparCarrinhoBtn = document.getElementById('limpar-carrinho-btn');
        

        const itensDisponiveis = {};
        document.querySelectorAll('.grid > div .btn-adicionar').forEach(button => {
            const card = button.closest('.item-card');
            const itemId = button.dataset.itemId;
            itensDisponiveis[itemId] = {
                nome: card.querySelector('[data-name]').textContent,
                codigo: card.querySelector('[data-code]').textContent.replace('Código: ', ''),
                categoria: card.querySelector('[data-category]').textContent.replace('Categoria: ', ''),
                disponivel: parseInt(card.querySelector('[data-disponivel]').textContent),
                valor: card.querySelector('[data-valor]').dataset.valor,
                imagem_url: card.querySelector('img').src
            };
        });

        function atualizarContador() {
            const itensNoCarrinho = retiradaContainer.querySelectorAll('.carrinho-item').length;
            contadorCarrinho.textContent = itensNoCarrinho;
            if (itensNoCarrinho > 0 && carrinhoVazioMensagem) {
                carrinhoVazioMensagem.classList.add('hidden');
            } else if (carrinhoVazioMensagem) {
                carrinhoVazioMensagem.classList.remove('hidden');
            }
        }

        if (limparCarrinhoBtn) {
    limparCarrinhoBtn.addEventListener('click', () => {
        // Pega a URL do atributo data-* que adicionamos
        const url = limparCarrinhoBtn.dataset.limparUrl;

        fetch(url, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrftoken,
                'Content-Type': 'application/json'
            },
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                console.log(data.message);
                
                // Limpa a exibição visual do carrinho
                // Encontra todos os itens no carrinho e os remove um por um
                const itensNoCarrinho = retiradaContainer.querySelectorAll('.carrinho-item');
                itensNoCarrinho.forEach(item => item.remove());
                
                // Atualiza o contador para 0 e mostra a mensagem de carrinho vazio
                if (contadorCarrinho) {
                    contadorCarrinho.textContent = '0';
                }
                if (carrinhoVazioMensagem) {
                    carrinhoVazioMensagem.classList.remove('hidden');
                }
                atualizarTotalCarrinho();
            }
        });
    });
}

        function adicionarAoCarrinho(itemId) {
            // Previne adicionar o mesmo item mais de uma vez
            if (retiradaContainer.querySelector(`.carrinho-item[data-item-id="${itemId}"]`)) {
                return; 
            }

            if (carrinhoVazioMensagem) {
                carrinhoVazioMensagem.classList.add('hidden');
            }

            const item = itensDisponiveis[itemId];
            const novoItem = carrinhoItemTemplate.content.cloneNode(true);
            const itemDiv = novoItem.querySelector('.carrinho-item');

            if (itemDiv) itemDiv.setAttribute('data-item-id', itemId);
            novoItem.querySelector('img').src = item.imagem_url;
            novoItem.querySelector('img').alt = `Imagem de ${item.nome}`;
            novoItem.querySelector('h4').textContent = item.nome;
            novoItem.querySelector('p').textContent = `Código: ${item.codigo}`;
            
            retiradaContainer.prepend(novoItem);
            atualizarContador();
            atualizarTotalCarrinho();

            if (popup) {
                popup.classList.remove('hidden');
                popup.classList.add('flex');
                }
            
            if (fecharPopupBtn) {
                fecharPopupBtn.addEventListener('click', () => {
                popup.classList.add('hidden');
                popup.classList.remove('flex');
                });
            
            } 
        }

        function atualizarTotalCarrinho() {
        let total = 0;
        const itensNoCarrinho = retiradaContainer.querySelectorAll('.carrinho-item');
        itensNoCarrinho.forEach(itemDiv => {
            const itemId = itemDiv.dataset.itemId;
            const quantidade = parseInt(itemDiv.querySelector('select').value);
            const itemInfo = itensDisponiveis[itemId];
            if (itemInfo && itemInfo.valor) {
                total += quantidade * parseFloat(itemInfo.valor);
            }
        });
        carrinhoTotalEl.textContent = `R$ ${total.toFixed(2).replace('.', ',')}`;
    }

        retiradaContainer.addEventListener('click', (event) => {
            const removerBtn = event.target.closest('.btn-remover');
            if (removerBtn) {
                const itemDiv = removerBtn.closest('.carrinho-item');
                if (itemDiv) {
                    itemDiv.remove();
                    atualizarContador();
                    atualizarTotalCarrinho();
                }
            }
        });

        retiradaContainer.addEventListener('change', (event) => {
            const select = event.target.closest('select');
            if (select) {
                const itemDiv = select.closest('.carrinho-item');
                if (!itemDiv) return;
                const itemId = itemDiv.dataset.itemId;
                const novaQuantidade = select.value;
                const url = retiradaContainer.dataset.updateUrl;

                fetch(url, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrftoken },
                    body: JSON.stringify({ 'item_id': itemId, 'quantidade': novaQuantidade }),
                })
                .then(res => res.json())
                .then(data => {
                if (data.status === 'success') {
                    console.log(data.message);
                    atualizarTotalCarrinho(); // CHAMADA CORRETA E PRINCIPAL
                }
            });
                
            }
        });

        botoesAdicionar.forEach(button => {
            button.addEventListener('click', () => {
                const itemId = button.dataset.itemId;
                const url = `/carrinho/adicionar/${itemId}/`;
                fetch(url, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrftoken },
                })
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'success') {
                        console.log(data.message);
                        adicionarAoCarrinho(itemId);
                        atualizarTotalCarrinho();
                    } else {
                        console.error('Erro:', data.message);
                    }
                });
            });
        });
        
        atualizarContador(); // Roda uma vez no início para esconder a mensagem se o carrinho já tiver itens
    }

    const graficoCanvas = document.getElementById('graficoGastosSemanais');
    
    if (graficoCanvas) {
        // Pega os dados que o Django inseriu na página
        const labels = JSON.parse(document.getElementById('chart-labels').textContent);
        const data = JSON.parse(document.getElementById('chart-data').textContent);

        new Chart(graficoCanvas, {
            type: 'bar', // Tipo do gráfico (pode ser 'line', 'pie', etc.)
            data: {
                labels: labels,
                datasets: [{
                    label: 'Valor Gasto (R$)',
                    data: data,
                    backgroundColor: 'rgba(59, 130, 246, 0.5)', // Cor das barras
                    borderColor: 'rgba(59, 130, 246, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            // Formata o eixo Y para mostrar "R$ 150,00"
                            callback: function(value, index, values) {
                                return 'R$ ' + value.toFixed(2).replace('.', ',');
                            }
                        }
                    }
                },
                plugins: {
                    tooltip: {
                        callbacks: {
                            // Formata a dica que aparece ao passar o mouse
                            label: function(context) {
                                let label = context.dataset.label || '';
                                if (label) {
                                    label += ': ';
                                }
                                if (context.parsed.y !== null) {
                                    label += 'R$ ' + context.parsed.y.toFixed(2).replace('.', ',');
                                }
                                return label;
                            }
                        }
                    }
                }
            }
        });
    }


    // --- BLOCO 2: LÓGICA DA PÁGINA DE HISTÓRICO (MODAL DE RECUSA) ---
    const modal = document.getElementById('recusar-modal');
    if (modal) {
        const modalForm = document.getElementById('recusar-form');
        const cancelarBtn = document.getElementById('cancelar-recusa-btn');
        const botoesRecusar = document.querySelectorAll('.btn-recusar');

        botoesRecusar.forEach(button => {
            button.addEventListener('click', () => {
                const retiradaId = button.dataset.retiradaId;
                modalForm.action = `/historico/recusar/${retiradaId}/`;
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
    
    // --- BLOCO 3: LÓGICA GLOBAL (SISTEMA DE NOTIFICAÇÕES NA NAVBAR) ---
    const notificacoesBtn = document.getElementById('notificacoes-btn');
    if (notificacoesBtn) {
        const notificacoesPanel = document.getElementById('notificacoes-panel');
        const notificacoesLista = document.getElementById('notificacoes-lista');
        const notificacaoBadge = document.getElementById('notificacao-badge');
        const notificacaoTemplate = document.getElementById('notificacao-template');
        const urlMarcarLido = notificacoesBtn.dataset.urlMarcarLido;
        const csrfTokenNotificacao = notificacoesBtn.dataset.csrfToken;
        let unreadNotifications = JSON.parse(document.getElementById('unread-notifications-data').textContent);

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

                    // Adiciona os itens à lista
                    notif.details.itens.forEach(itemText => {
                        const li = document.createElement('li');
                        li.textContent = itemText;
                        itemList.appendChild(li);
                    });

                    // Adiciona o motivo
                    reasonText.textContent = notif.details.motivo;
                    
                    // Mostra as seções de detalhes e motivo
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
                        unreadNotifications.length = 0;
                    }
                });
            }
        });
    }
});