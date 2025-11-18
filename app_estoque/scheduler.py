import threading
import time
from django.utils import timezone
from app_estoque.models import Item
from django.core.mail import send_mail


INTERVALO = 60  # 1 minuto para testar

def tarefa_periodica():
    while True:
        print("Tarefa agendada executada:", timezone.now())

        itens_zerados = Item.objects.filter(disponivel__lte=0)
        if itens_zerados.exists():

            lista_itens = "\n".join(
                [f"{item.nome} ({item.codigo})" for item in itens_zerados]
            )

            send_mail(
                subject="⚠️ Alerta: Itens zerados",
                message=f"Os seguintes itens estão com estoque zerado:\n\n{lista_itens}",
                from_email=None,  # usa DEFAULT_FROM_EMAIL
                recipient_list=["SEU_EMAIL@gmail.com"],  # email que vai receber
                fail_silently=False
            )

            print("Email enviado com sucesso!")

        time.sleep(INTERVALO)

def iniciar_scheduler():
    thread = threading.Thread(target=tarefa_periodica, daemon=True)
    thread.start()