from django.core.mail import send_mail
from django.contrib.auth.models import User
from .models import Item

def verificar_itens_zerados():
    # Enviar alerta se estoque <= 5
    itens_zerados = Item.objects.filter(disponivel__lte=5)

    if not itens_zerados.exists():
        return

    lista = "\n".join([f"{item.nome} (Código: {item.codigo})" for item in itens_zerados])

    assunto = "⚠ Alerta: Estoque baixo"
    corpo = (
        "Atenção Supervisor,\n\n"
        "Os seguintes itens estão com quantidade baixa no estoque:\n\n"
        f"{lista}\n\n"
        "Por favor, verificar a necessidade de reposição.\n\n"
        "Mensagem automática do Sistema de Estoque."
    )

    # Pega SOMENTE usuários que são supervisores e têm email cadastrado
    supervisores = User.objects.filter(groups__name="Supervisores")\
                               .exclude(email__isnull=True)\
                               .exclude(email="")

    emails = list(supervisores.values_list("email", flat=True))

    if not emails:
        print("⚠ Nenhum supervisor com email cadastrado.")
        return

    send_mail(
        subject=assunto,
        message=corpo,
        from_email=None,
        recipient_list=emails,
        fail_silently=False
    )

    print("📨 Email enviado aos supervisores.")
