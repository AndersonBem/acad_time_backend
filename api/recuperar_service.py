import secrets
from datetime import timedelta
from django.conf import settings

from django.core.mail import send_mail
from django.utils import timezone

from api.models import Usuario, RecuperacaoSenha
from api.email_service import enviar_email_resend

class RecuperacaoSenhaService:
    @staticmethod
    def solicitar_recuperacao(email):
        try:
            usuario = Usuario.objects.get(email=email)
        except Usuario.DoesNotExist:
            return

        RecuperacaoSenha.objects.filter(
            usuario=usuario,
            usado=False
        ).update(usado=True)

        token = secrets.token_urlsafe(32)
        expira_em = timezone.now() + timedelta(hours=1)

        RecuperacaoSenha.objects.create(
            usuario=usuario,
            token=token,
            expira_em=expira_em,
            usado=False,
            data_criacao=timezone.now()
        )

        link = f'{settings.FRONTEND_URL}/pages/redefinirsenha.html?token={token}'

        assunto = 'AcadTime - Recuperação de senha'

        html = f"""
        <h2>Recuperação de senha</h2>
        <p>Olá, {usuario.nome}.</p>
        <p>Recebemos uma solicitação para redefinir sua senha.</p>
        <p>
            Clique no link abaixo para continuar:<br>
            <a href="{link}">{link}</a>
        </p>
        <p>Esse link expira em 1 hora.</p>
        <p>Se você não solicitou isso, ignore este e-mail.</p>
        """

        texto = (
            f'Olá, {usuario.nome}.\n\n'
            f'Recebemos uma solicitação para redefinir sua senha.\n\n'
            f'Acesse o link abaixo para continuar:\n'
            f'{link}\n\n'
            f'Esse link expira em 1 hora.\n\n'
            f'Se você não solicitou isso, ignore este e-mail.'
        )

        enviar_email_resend(
            destinatario=usuario.email,
            assunto=assunto,
            html=html,
            texto=texto
        )