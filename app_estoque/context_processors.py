import json
from .models import Notificacao
from django.core.serializers import serialize

def unread_notifications(request):
    if request.user.is_authenticated:
        notifications_qs = Notificacao.objects.filter(
            usuario=request.user, lida=False
        ).select_related('retirada_associada')

        notifications_data = []
        for notif in notifications_qs:
            data = {
                'mensagem': notif.mensagem,
                'data_criacao': notif.data_criacao.isoformat(),
                'details': None  # Começa sem detalhes
            }

            # Se a notificação for de uma retirada recusada, adiciona os detalhes
            if notif.retirada_associada and notif.retirada_associada.status == 'RECUSADA':
                items_list = []
                for item_retirado in notif.retirada_associada.itens_retirados.all():
                    items_list.append(
                        f"{item_retirado.quantidade}x {item_retirado.item.nome} ({item_retirado.item.codigo})"
                    )

                data['details'] = {
                    'itens': items_list,
                    'motivo': notif.retirada_associada.motivo_recusa
                }

            notifications_data.append(data)

        return {
            'unread_notifications_data': notifications_data,
            'unread_notifications_count': notifications_qs.count()
        }
    return {}