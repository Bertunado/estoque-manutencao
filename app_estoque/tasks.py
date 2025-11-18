from django.core.mail import send_mail
from django.contrib.auth.models import User
from .models import Item

def verificar_itens_zerados():
    itens_zerados = Item.objects.filter(disponivel=0)

    if not itens_zerados.exists():
        return  # Nenhum item com quantidade = 0 → não envia email

    # Lista os itens zerados no corpo do email
    lista = "\n".join([f"{item.nome} (Código: {item.codigo})" for item in itens_zerados])

    assunto = "⚠ Itens zerados no estoque"
    corpo = (
        "Atenção Supervisor,\n\n"
        "Os seguintes itens estão com quantidade igual a ZERO:\n\n"
        f"{lista}\n\n"
        "Por favor, verificar a necessidade de reposição.\n\n"
        "Mensagem automática do Sistema de Estoque."
    )

    # Buscar todos os supervisores
    supervisores = User.objects.filter(groups__name="Supervisores")

    emails = [user.email for user in supervisores if user.email]

    if not emails:
        return  # Não há supervisores com email cadastrado

    # Enviar o email
    send_mail(
        subject=assunto,
        message=corpo,
        from_email=None,  # usa DEFAULT_FROM_EMAIL
        recipient_list=emails,
        fail_silently=False
    )

    print("📨 Email enviado aos supervisores.")
