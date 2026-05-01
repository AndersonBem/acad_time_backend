import resend
from django.conf import settings


def enviar_email_resend(destinatario, assunto, html, texto=None):
    """
    Envia um e-mail usando a API HTTP do Resend.
    Retorna a resposta da API em caso de sucesso.
    Lança exceção em caso de erro.
    """

    if not settings.RESEND_API_KEY:
        raise ValueError('RESEND_API_KEY não configurada.')

    resend.api_key = settings.RESEND_API_KEY

    payload = {
        "from": settings.RESEND_FROM_EMAIL,
        "to": [destinatario] if isinstance(destinatario, str) else destinatario,
        "subject": assunto,
        "html": html,
    }

    if texto:
        payload["text"] = texto

    resposta = resend.Emails.send(payload)
    return resposta