from django.core.mail import send_mail
from django.utils import timezone

from api.models import NotificacaoEmail
from api.email_service import enviar_email_resend


class NotificacaoService:
    STATUS_SUCESSO = 'SUCESSO'
    STATUS_FALHA = 'FALHA'

    EVENTO_SUBMISSAO_CRIADA = 'SUBMISSAO_CRIADA'
    EVENTO_SUBMISSAO_APROVADA = 'SUBMISSAO_APROVADA'
    EVENTO_SUBMISSAO_REPROVADA = 'SUBMISSAO_REPROVADA'

    @staticmethod
    def _registrar_notificacao(submissao, assunto, corpo, destinatario, tipo_evento, status_envio, mensagem_erro=None):
        NotificacaoEmail.objects.create(
            assunto=assunto,
            corpo=corpo,
            data=timezone.now().date(),
            destinatario=destinatario,
            status_envio=status_envio,
            tipo_evento=tipo_evento,
            mensagem_erro=mensagem_erro,
            submissao=submissao
        )

    @staticmethod
    def _enviar_email(submissao, assunto, corpo, destinatario, tipo_evento):
        try:
            html = corpo.replace('\n', '<br>')

            enviar_email_resend(
                destinatario=destinatario,
                assunto=assunto,
                html=html,
                texto=corpo
            )

            NotificacaoService._registrar_notificacao(
                submissao=submissao,
                assunto=assunto,
                corpo=corpo,
                destinatario=destinatario,
                tipo_evento=tipo_evento,
                status_envio=NotificacaoService.STATUS_SUCESSO
            )

        except Exception as e:
            NotificacaoService._registrar_notificacao(
                submissao=submissao,
                assunto=assunto,
                corpo=corpo,
                destinatario=destinatario,
                tipo_evento=tipo_evento,
                status_envio=NotificacaoService.STATUS_FALHA,
                mensagem_erro=str(e)
            )
            raise

    @staticmethod
    def notificar_submissao_criada(submissao):
        coordenador_usuario = submissao.coordenador.usuario
        aluno_usuario = submissao.aluno.usuario

        assunto = f'Nova submissão pendente - {submissao.curso.nome}'
        corpo = (
            f'Olá, {coordenador_usuario.nome}.\n\n'
            f'O aluno {aluno_usuario.nome} realizou uma nova submissão para o curso {submissao.curso.nome}.\n\n'
            f'Status atual: {submissao.status_submissao.nome_status}.\n'
            f'ID da submissão: {submissao.id_submissao}.'
        )

        NotificacaoService._enviar_email(
            submissao=submissao,
            assunto=assunto,
            corpo=corpo,
            destinatario=coordenador_usuario.email,
            tipo_evento=NotificacaoService.EVENTO_SUBMISSAO_CRIADA
        )

    @staticmethod
    def notificar_submissao_aprovada(submissao):
        aluno_usuario = submissao.aluno.usuario

        assunto = f'Submissão aprovada - {submissao.curso.nome}'
        corpo = (
            f'Olá, {aluno_usuario.nome}.\n\n'
            f'Sua submissão de ID {submissao.id_submissao} foi aprovada no curso {submissao.curso.nome}.\n\n'
            f'Carga horária aprovada: {submissao.carga_horaria_aprovada}.'
        )

        NotificacaoService._enviar_email(
            submissao=submissao,
            assunto=assunto,
            corpo=corpo,
            destinatario=aluno_usuario.email,
            tipo_evento=NotificacaoService.EVENTO_SUBMISSAO_APROVADA
        )

    @staticmethod
    def notificar_submissao_reprovada(submissao):
        aluno_usuario = submissao.aluno.usuario

        assunto = f'Submissão reprovada - {submissao.curso.nome}'
        corpo = (
            f'Olá, {aluno_usuario.nome}.\n\n'
            f'Sua submissão de ID {submissao.id_submissao} foi reprovada no curso {submissao.curso.nome}.\n\n'
            f'Observação do coordenador: {submissao.observacao_coordenador or "Não informada"}'
        )

        NotificacaoService._enviar_email(
            submissao=submissao,
            assunto=assunto,
            corpo=corpo,
            destinatario=aluno_usuario.email,
            tipo_evento=NotificacaoService.EVENTO_SUBMISSAO_REPROVADA
        )