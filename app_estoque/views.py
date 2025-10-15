from django.utils import timezone
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.http import JsonResponse
from .models import Item, Retirada, ItemRetirado, Notificacao
from .forms import ItemForm, CustomUserCreationForm
from django.contrib.auth import login
import json
from django.db.models import Q, Sum, F, Value, DecimalField
from django.core.paginator import Paginator
from django.db.models.functions import TruncWeek, Coalesce
from datetime import timedelta
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.utils.dateparse import parse_datetime

@login_required
def retirada_itens(request):
    query = request.GET.get('q')
    
    # Começa com a regra base: apenas itens com estoque > 0
    base_itens = Item.objects.filter(disponivel__gt=0)

    if query:
        # Aplica o filtro de busca sobre a lista de itens já disponíveis
        item_list = base_itens.filter(
            Q(nome__icontains=query) | Q(codigo__icontains=query)
        ).order_by('nome')
    else:
        # Se não houver busca, usa a lista completa de itens disponíveis
        item_list = base_itens.order_by('nome')
    
    # LÓGICA DE PAGINAÇÃO
    paginator = Paginator(item_list, 12)# Define 9 itens por página
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj  # Envia o page_obj para o template
    }
    return render(request, 'retirada_itens.html', context)

@login_required
def estoque_view(request):
    query = request.GET.get('q')
    
    if query:
        item_list = Item.objects.filter(
            Q(nome__icontains=query) | Q(codigo__icontains=query)
        ).order_by('nome')
    else:
        item_list = Item.objects.all().order_by('nome') 
    
    paginator = Paginator(item_list, 12) 
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj 
    }
    
    return render(request, 'estoque.html', context)

@login_required
def carrinho_view(request):
    carrinho_session = request.session.get('carrinho', {})
    
    itens_no_carrinho = []
    valor_total_carrinho = 0
    
    # Busca os objetos 'Item' completos com base nos IDs do carrinho
    item_ids = carrinho_session.keys()
    itens_db = Item.objects.filter(id__in=item_ids)
    
    for item in itens_db:
        item_id_str = str(item.id)
        quantidade = carrinho_session[item_id_str]['quantidade']
        valor_item_total = item.valor * quantidade
        
        itens_no_carrinho.append({
            'item': item,
            'quantidade': quantidade,
            'valor_total': valor_item_total,
        })
        valor_total_carrinho += valor_item_total

    context = {
        'itens_no_carrinho': itens_no_carrinho,
        'valor_total_carrinho': valor_total_carrinho,
    }
    return render(request, 'carrinho.html', context)

@login_required
def limpar_carrinho(request):
    if 'carrinho' in request.session:
        del request.session['carrinho']
    return JsonResponse({'status': 'success', 'message': 'Carrinho limpo.'})

@login_required
@permission_required('app_estoque.view_retirada', raise_exception=True) # Protegido para supervisores
def dashboard_view(request):
    # Pega as retiradas APROVADAS dos últimos 3 meses
    tres_meses_atras = timezone.now() - timedelta(days=90)
    
    gastos_semanais = Retirada.objects.filter(
        status='APROVADA',
        data_retirada__gte=tres_meses_atras
    ).annotate(
        week=TruncWeek('data_retirada')
    ).values('week').annotate(
        total_gasto=Coalesce(
            Sum(F('itens_retirados__quantidade') * F('itens_retirados__item__valor')),
            Value(0),
            output_field=DecimalField()
        )
    ).order_by('week')

    # Formata os dados para o Chart.js
    chart_labels = [g['week'].strftime('%d/%m/%Y') for g in gastos_semanais]
    chart_data = [float(g['total_gasto']) for g in gastos_semanais]

    context = {
        'chart_labels': chart_labels,
        'chart_data': chart_data,
    }
    
    return render(request, 'dashboard.html', context)

@login_required
def verificar_novas_retiradas(request):
    # Pega o horário da última verificação, enviado pelo JavaScript
    ultimo_timestamp_str = request.GET.get('since', None)
    
    if not ultimo_timestamp_str:
        return JsonResponse({'novas_retiradas': False})

    ultimo_timestamp = parse_datetime(ultimo_timestamp_str)

    # Verifica se existe alguma retirada PENDENTE criada DEPOIS da última verificação
    ha_novas_retiradas = Retirada.objects.filter(
        status='PENDENTE',
        data_retirada__gt=ultimo_timestamp
    ).exists()
    
    return JsonResponse({'novas_retiradas': ha_novas_retiradas})

@login_required
def atualizar_quantidade_carrinho(request):
    if request.method == 'POST':
        # Carrega os dados enviados pelo JavaScript
        data = json.loads(request.body)
        item_id = str(data.get('item_id'))
        nova_quantidade = int(data.get('quantidade'))

        carrinho = request.session.get('carrinho', {})

        # Atualiza a quantidade do item específico no carrinho
        if item_id in carrinho and nova_quantidade > 0:
            carrinho[item_id]['quantidade'] = nova_quantidade
            request.session['carrinho'] = carrinho # Salva o carrinho atualizado na sessão
            return JsonResponse({'status': 'success', 'message': 'Quantidade atualizada.'})

    return JsonResponse({'status': 'error', 'message': 'Requisição inválida.'}, status=400)

@login_required
@permission_required('app_estoque.change_item', raise_exception=True)
def editar_item(request, item_id):
    item = get_object_or_404(Item, id=item_id)

    if request.method == 'POST':
        form = ItemForm(request.POST, request.FILES, instance=item)
        if form.is_valid():
            # Pega a quantidade a ser adicionada do nosso novo campo
            quantidade_a_adicionar = form.cleaned_data.get('adicionar_quantidade', 0)
            
            # Salva as outras alterações (nome, código, etc.) mas NÃO envia para o banco ainda
            item_atualizado = form.save(commit=False)

            # Se o usuário digitou um valor para adicionar, faz a soma
            if quantidade_a_adicionar and quantidade_a_adicionar > 0:
                item_atualizado.disponivel += quantidade_a_adicionar
            
            # Agora sim, salva o objeto completo no banco de dados
            item_atualizado.save()
            
            return redirect('estoque:estoque_lista')
    else:
        form = ItemForm(instance=item)

    context = {
        'form': form,
        'item': item
    }
    return render(request, 'editar_item.html', context)

# NOVA VIEW: Lógica para adicionar item ao carrinho na sessão
def adicionar_ao_carrinho(request, item_id):
    # Garante que a requisição seja do tipo POST por segurança
    if request.method == 'POST':
        # Pega o carrinho da sessão ou cria um dicionário vazio
        carrinho = request.session.get('carrinho', {})
        
        item = get_object_or_404(Item, id=item_id)
        item_id_str = str(item_id) # Chaves de dicionário devem ser strings

        # Por enquanto, vamos adicionar apenas 1 unidade de cada item
        if item_id_str not in carrinho:
            carrinho[item_id_str] = {
                'nome': item.nome,
                'codigo': item.codigo,
                'quantidade': 1 # Começa com 1
            }
        
        # Salva o carrinho de volta na sessão
        request.session['carrinho'] = carrinho
        
        # Retorna uma resposta de sucesso com os dados do carrinho atualizado
        return JsonResponse({
            'status': 'success', 
            'message': f'"{item.nome}" adicionado com sucesso!',
            'carrinho': carrinho,
            'total_itens': len(carrinho)
        })
    
    return JsonResponse({'status': 'error', 'message': 'Requisição inválida.'})

@login_required
@permission_required('app_estoque.add_item', raise_exception=True)
def adicionar_item(request):
    if request.method == 'POST':
        # Se o formulário foi enviado, processa os dados
        form = ItemForm(request.POST, request.FILES) # request.FILES é para a imagem
        if form.is_valid():
            form.save() # Salva o novo item no banco de dados
            return redirect('estoque:estoque_lista') # Redireciona para a lista de estoque
    else:
        form = ItemForm()
    
    context = {
        'form': form
    }
    return render(request, 'adicionar_item.html', context)

@login_required
@permission_required('app_estoque.change_retirada', raise_exception=True)
def recusar_retirada(request, retirada_id):
    if request.method == 'POST':
        retirada = get_object_or_404(Retirada, id=retirada_id)
        
        motivo = request.POST.get('motivo_recusa', 'Motivo não especificado.')

        retirada.status = 'RECUSADA'
        retirada.motivo_recusa = motivo
        retirada.save()
        
        mensagem_notificacao = "Sua solicitação de retirada foi recusada."

        Notificacao.objects.create(
            usuario=retirada.usuario,
            retirada_associada=retirada,
            mensagem=mensagem_notificacao
        )

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'user_{retirada.usuario.id}', # Envia para o grupo específico do usuário
            {
                "type": "send.notification",
                "message": mensagem_notificacao
            }
        )

    return redirect('estoque:historico')

@login_required
def confirmar_retirada(request):
    if request.method == 'POST':
        carrinho = request.session.get('carrinho', {})
        observacao = request.POST.get('observacao', '')

        if not carrinho:
            return redirect('estoque:retirada')

        nova_retirada = Retirada.objects.create(
            usuario=request.user,
            observacao=observacao,
            status='PENDENTE' # Status inicial
        )

        # 2. Loop para salvar cada item retirado (SEM ALTERAR O ESTOQUE)
        for item_id, dados in carrinho.items():
            item = get_object_or_404(Item, id=item_id)
            quantidade_retirada = dados['quantidade']

            ItemRetirado.objects.create(
                retirada=nova_retirada,
                item=item,
                quantidade=quantidade_retirada
            )
        
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "historico_geral",
            {
                "type": "notificar.nova.retirada",
                "message": "Uma nova retirada foi solicitada e está pendente de aprovação."
            }
        )

        
        
        del request.session['carrinho']
        return redirect('estoque:historico')
    
    return redirect('estoque:retirada')

@login_required
@permission_required('app_estoque.change_retirada', raise_exception=True) # Proteção para supervisores
def aprovar_retirada(request, retirada_id):
    if request.method == 'POST':
        retirada = get_object_or_404(Retirada, id=retirada_id)
        
        # 1. Atualiza o estoque para cada item na retirada
        for item_retirado in retirada.itens_retirados.all():
            item = item_retirado.item
            item.disponivel -= item_retirado.quantidade
            item.save()

        # 2. Muda o status da retirada para APROVADA
        retirada.status = 'APROVADA'
        retirada.save()

        primeiro_item = retirada.itens_retirados.first().item.nome
        mensagem_notificacao = f"Sua retirada contendo '{primeiro_item}' foi aprovada."

        # Cria a notificação para o usuário que SOLICITOU a retirada
        Notificacao.objects.create(
            usuario=retirada.usuario, # O usuário original da retirada
            retirada_associada=retirada,
            mensagem=mensagem_notificacao
        )

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'user_{retirada.usuario.id}', # Envia para o grupo específico do usuário
            {
                "type": "send.notification",
                "message": mensagem_notificacao
            }
        )

    return redirect('estoque:historico')

@login_required
def marcar_notificacoes_como_lidas(request):
    if request.method == 'POST':
        Notificacao.objects.filter(usuario=request.user, lida=False).update(lida=True)
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)

@login_required
def historico_view(request):
    query = request.GET.get('q')
    
    is_supervisor = request.user.groups.filter(name='Supervisores').exists()
    
    if is_supervisor:
        base_historico = Retirada.objects.all()
    else:
        base_historico = Retirada.objects.filter(usuario=request.user)

    if query:
        # LÓGICA DE BUSCA COMPLETA (substituindo o '...')
        retirada_list = base_historico.filter(
            Q(usuario__username__icontains=query) |
            Q(usuario__first_name__icontains=query) |
            Q(usuario__last_name__icontains=query)
        )
    else:
        retirada_list = base_historico

    # LÓGICA DE OTIMIZAÇÃO COMPLETA (substituindo o '...')
    retirada_list = retirada_list.select_related('usuario').prefetch_related('itens_retirados__item').order_by('-data_retirada')
    
    # Lógica de paginação
    paginator = Paginator(retirada_list, 5) 
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'is_supervisor': is_supervisor
    }
    return render(request, 'historico.html', context)

def cadastro_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save() # Salva o novo usuário no banco
            login(request, user) # Faz o login automático do usuário recém-criado
            return redirect('estoque:estoque_lista') # Redireciona para a página de estoque
    else:
        form = CustomUserCreationForm()
    
    context = {
        'form': form
    }
    return render(request, 'cadastro.html', context)