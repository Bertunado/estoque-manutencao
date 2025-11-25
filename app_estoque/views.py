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
from django.contrib.auth.decorators import user_passes_test, login_required
from django.http import HttpResponse, Http404, FileResponse, HttpResponseForbidden
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.lib import colors
import csv
from io import BytesIO
from datetime import datetime
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle
from babel.numbers import format_currency
from .forms import PerfilForm
from django.contrib import messages
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings



def enviar_alerta_estoque_baixo(itens_afetados):
    """
    Recebe uma lista de objetos Item que ficaram com estoque baixo e envia e-mail.
    """
    if not itens_afetados:
        return

    # Busca e-mails dos supervisores
    supervisores = User.objects.filter(groups__name="Supervisores")
    emails = list(supervisores.exclude(email='').values_list("email", flat=True))

    if not emails:

        print("⚠️ Alerta de estoque: Nenhum supervisor com e-mail cadastrado.")
        return

    # Monta a lista de itens para o corpo do e-mail
    lista_texto = "\n".join([f"- {i.nome} (Cód: {i.codigo}) | Restam: {i.disponivel}" for i in itens_afetados])

    assunto = "⚠️ Alerta: Itens com Estoque Baixo"
    corpo = (
        "Atenção Supervisor,\n\n"
        "Os seguintes itens atingiram o nível crítico de estoque (15 ou menos) após a última retirada:\n\n"
        f"{lista_texto}\n\n"
        "Acesse o sistema para providenciar a reposição.\n"
        "Mensagem automática do Sistema de Estoque."
    )

    try:
        send_mail(
            subject=assunto,
            message=corpo,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=emails,
            fail_silently=False
        )
        print(f"E-mail de alerta enviado para: {emails}")
    except Exception as e:
        print(f"rro ao enviar e-mail: {e}")


@login_required
@permission_required('app_estoque.delete_item', raise_exception=True)
def excluir_item(request, item_id):
    item = get_object_or_404(Item, id=item_id)
    if request.method == 'POST':
        nome_item = item.nome
        item.delete()
        messages.success(request, f"Item '{nome_item}' excluído com sucesso.")
        return redirect('estoque:estoque_lista')
    return redirect('estoque:estoque_lista')

@login_required
def perfil_view(request):
    """
    Página para o usuário editar seu perfil .
    """
    user = request.user

    if request.method == 'POST':
        form = PerfilForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, "Perfil atualizado com sucesso.")
            return redirect('estoque:perfil')
        else:
            messages.error(request, "Por favor corrija os erros no formulário.")
    else:
        form = PerfilForm(instance=user)

    context = {
        'form': form
    }
    return render(request, 'perfil.html', context)

@login_required
def configuracoes_perfil(request):
    user = request.user

    if request.method == 'POST':
        form = PerfilForm(request.POST, instance=user)

        if form.is_valid():
            form.save()

            if user.groups.filter(name='Supervisores').exists():
                messages.success(request, "Perfil atualizado. Como supervisor, seu email será usado para notificações automáticas.")
            else:
                messages.warning(request, "Perfil atualizado. Porém, apenas supervisores recebem notificações automáticas.")

            return redirect('estoque:configuracoes')

    else:
        form = PerfilForm(instance=user)

    return render(request, "configuracoes.html", {'form': form})



@login_required
def retirada_itens(request):
    query = request.GET.get('q')

    base_itens = Item.objects.filter(disponivel__gt=0)

    if query:
        item_list = base_itens.filter(
            Q(nome__icontains=query) | Q(codigo__icontains=query)
        ).order_by('nome')
    else:
        item_list = base_itens.order_by('nome')

    # LÓGICA DE PAGINAÇÃO
    paginator = Paginator(item_list, 12)# Define 9 itens por página
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj
    }
    return render(request, 'retirada_itens.html', context)

@login_required
def exportar_csv_retiradas(request):
    """Permite que o supervisor exporte TODAS as retiradas em CSV."""

    user = request.user

    is_supervisor = user.is_superuser or user.groups.filter(name='Supervisores').exists()

    if is_supervisor:
        # Se for supervisor, pega TUDO do banco
        retiradas = Retirada.objects.all()
        filename = "relatorio_geral_completo.csv"
    else:
        # Se for usuário comum, pega apenas as DELE
        retiradas = Retirada.objects.filter(usuario=user)
        filename = "meu_historico_retiradas.csv"

    retiradas = retiradas.select_related('usuario').prefetch_related('itens_retirados__item').order_by('-data_retirada')

    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    response.write(u'\ufeff'.encode('utf8'))

    writer = csv.writer(response, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)

    # Cabeçalho
    writer.writerow([
        "Solicitante",
        "Data da Retirada",
        "Status",
        "Itens Retirados",
        "Valor Total (R$)",
        "Observação"
    ])

    for retirada in retiradas:
        lista_itens = []
        for item_retirado in retirada.itens_retirados.all():
            lista_itens.append(f"{item_retirado.quantidade}x {item_retirado.item.nome}")

        texto_itens = " | ".join(lista_itens)

        valor_formatado = f"{retirada.valor_total:.2f}".replace('.', ',')

        if retirada.data_retirada:
            data_local = timezone.localtime(retirada.data_retirada)
            data_formatada = data_local.strftime("%d/%m/%Y %H:%M")
        else:
            data_formatada = "--"

        nome_usuario = retirada.usuario.get_full_name()
        if not nome_usuario:
            nome_usuario = retirada.usuario.username

        writer.writerow([
            nome_usuario,
            data_formatada,
            retirada.get_status_display(),
            texto_itens,
            valor_formatado,
            retirada.observacao or ""
        ])

    return response

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
@permission_required('app_estoque.view_retirada', raise_exception=True)
def dashboard_view(request):
    ano_atual = datetime.now().year
    meses_nomes = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']

    # Estruturas para armazenar os dados
    totais_anuais = [0.0] * 12

    detalhes_semanais = {i: {} for i in range(12)}

    # Busca todas as retiradas APROVADAS do ano atual
    retiradas = Retirada.objects.filter(
        status='APROVADA',
        data_retirada__year=ano_atual
    ).select_related('usuario').prefetch_related('itens_retirados__item').order_by('data_retirada')

    for retirada in retiradas:
        mes_idx = retirada.data_retirada.month - 1  # 0 = Janeiro

        semana_inicio = retirada.data_retirada.strftime('%W')
        label_semana = f"Semana {retirada.data_retirada.strftime('%d/%m')}"

        valor = float(retirada.valor_total)

        totais_anuais[mes_idx] += valor

        if label_semana in detalhes_semanais[mes_idx]:
            detalhes_semanais[mes_idx][label_semana] += valor
        else:
            detalhes_semanais[mes_idx][label_semana] = valor

    dados_semanais_final = {}
    for mes_idx, semanas_dict in detalhes_semanais.items():
        dados_semanais_final[mes_idx] = {
            'labels': list(semanas_dict.keys()),
            'data': list(semanas_dict.values())
        }

    context = {
        'ano_atual': ano_atual,
        'meses_labels': json.dumps(meses_nomes),
        'meses_data': json.dumps(totais_anuais),
        'semanas_detalhes': json.dumps(dados_semanais_final),
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
            quantidade_a_adicionar = form.cleaned_data.get('adicionar_quantidade', 0)

            # Salva as outras alterações (nome, código, etc.) mas NÃO envia para o banco ainda
            item_atualizado = form.save(commit=False)

            # Se o usuário digitou um valor para adicionar, faz a soma
            if quantidade_a_adicionar and quantidade_a_adicionar > 0:
                item_atualizado.disponivel += quantidade_a_adicionar

            # Agora salva o objeto completo no banco de dados
            item_atualizado.save()

            return redirect('estoque:estoque_lista')
    else:
        form = ItemForm(instance=item)

    context = {
        'form': form,
        'item': item
    }
    return render(request, 'editar_item.html', context)

def adicionar_ao_carrinho(request, item_id):
    if request.method == 'POST':
        # Pega o carrinho da sessão ou cria um dicionário vazio
        carrinho = request.session.get('carrinho', {})

        item = get_object_or_404(Item, id=item_id)
        item_id_str = str(item_id)

        if item_id_str not in carrinho:
            carrinho[item_id_str] = {
                'nome': item.nome,
                'codigo': item.codigo,
                'quantidade': 1
            }

        # Salva o carrinho de volta na sessão
        request.session['carrinho'] = carrinho

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
        form = ItemForm(request.POST, request.FILES)
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
            f'user_{retirada.usuario.id}',
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
@permission_required('app_estoque.change_retirada', raise_exception=True)
def aprovar_retirada(request, retirada_id):
    if request.method == 'POST':
        retirada = get_object_or_404(Retirada, id=retirada_id)

        itens_com_estoque_baixo = [] # Lista para acumular itens críticos

        for item_retirado in retirada.itens_retirados.all():
            item = item_retirado.item
            item.disponivel -= item_retirado.quantidade
            item.save()

            # Verifica se baixou para 15 ou menos (<= 15)
            if item.disponivel <= 15:
                itens_com_estoque_baixo.append(item)

        # Envia E-MAIL SE houver itens críticos
        if itens_com_estoque_baixo:
            enviar_alerta_estoque_baixo(itens_com_estoque_baixo)

        retirada.status = 'APROVADA'
        retirada.save()

        primeiro_item = retirada.itens_retirados.first().item.nome
        mensagem_notificacao = f"Sua retirada contendo '{primeiro_item}' foi aprovada."
        Notificacao.objects.create(usuario=retirada.usuario, retirada_associada=retirada, mensagem=mensagem_notificacao)

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(f'user_{retirada.usuario.id}', {"type": "send.notification", "message": mensagem_notificacao})

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
        retirada_list = base_historico.filter(
            Q(usuario__username__icontains=query) |
            Q(usuario__first_name__icontains=query) |
            Q(usuario__last_name__icontains=query)
        )
    else:
        retirada_list = base_historico

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



def is_supervisor(user):
    """Verifica se o usuário pertence ao grupo Supervisores"""
    return user.groups.filter(name='Supervisores').exists()

@user_passes_test(is_supervisor)
def gerar_pdf_retirada(request, retirada_id):
    retirada = Retirada.objects.get(id=retirada_id)

    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    vermelho = colors.HexColor("#d61c1c")
    cinza_claro = colors.HexColor("#f5f5f5")
    preto = colors.HexColor("#333333")

    p.setFont("Helvetica-Bold", 18)
    p.setFillColor(vermelho)
    p.drawString(40, height - 60, "Comprovante")

    p.setFillColor(preto)
    p.setFont("Helvetica-Bold", 14)
    p.drawCentredString(width / 2, height - 90, "Comprovante de Retirada")

    p.setFont("Helvetica", 10)
    p.setFillColor(colors.gray)
    data_emissao = datetime.now().strftime("%d/%m/%Y • %H:%M:%S")
    p.drawCentredString(width / 2, height - 105, f"Emitido em {data_emissao}")

    p.setStrokeColor(colors.lightgrey)
    p.line(40, height - 115, width - 40, height - 115)

    y = height - 150

    def secao(titulo, valor):
        nonlocal y
        p.setFont("Helvetica-Bold", 10)
        p.setFillColor(vermelho)
        p.drawString(40, y, titulo)
        y -= 12
        p.setFont("Helvetica", 10)
        p.setFillColor(preto)
        p.drawString(40, y, valor)
        y -= 20

    secao("Nome do Solicitante", retirada.usuario.get_full_name() or retirada.usuario.username)
    secao("Data da Retirada", retirada.data_retirada.strftime("%d/%m/%Y • %H:%M"))
    secao("Status", retirada.status)

    if retirada.observacao:
        secao("Observação", retirada.observacao)

    y -= 5
    p.setFont("Helvetica-Bold", 10)
    p.setFillColor(vermelho)
    p.drawString(40, y, "Itens Retirados:")
    y -= 15

    data = [["Qtd", "Item", "Código", "Valor Unitário (R$)", "Subtotal (R$)"]]

    for item in retirada.itens_retirados.all():
        valor_unitario = item.item.valor or 0
        subtotal = item.quantidade * valor_unitario

        data.append([
            str(item.quantidade),
            item.item.nome,
            item.item.codigo,
            format_currency(valor_unitario, 'BRL', locale='pt_BR'),
            format_currency(subtotal, 'BRL', locale='pt_BR')
        ])

    tabela = Table(data, colWidths=[40, 160, 70, 100, 90])
    tabela.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), vermelho),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.gray),
        ("BACKGROUND", (0, 1), (-1, -1), colors.whitesmoke),
    ]))

    w, h = tabela.wrapOn(p, width - 80, y)
    tabela.drawOn(p, 40, y - h)
    y -= h + 20

    p.setFont("Helvetica-Bold", 11)
    p.setFillColor(preto)
    p.drawRightString(width - 40, y, f"Valor Total: R$ {retirada.valor_total:.2f}")

    y -= 40
    p.setStrokeColor(colors.lightgrey)
    p.line(40, y, width - 40, y)
    y -= 15
    p.setFont("Helvetica", 9)
    p.setFillColor(colors.gray)
    p.drawCentredString(width / 2, y, "Documento gerado automaticamente pelo Sistema de Controle de Estoque")

    p.showPage()
    p.save()
    buffer.seek(0)

    filename = f"comprovante_retirada_{retirada.id}.pdf"
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response

@login_required
def visualizar_pdf(request, id):
    retirada = get_object_or_404(Retirada, id=id)

    if retirada.status == "recusada":
        return HttpResponseForbidden("PDF indisponível — retirada recusada")

    return FileResponse(open(retirada.arquivo_pdf.path, "rb"), content_type="application/pdf")