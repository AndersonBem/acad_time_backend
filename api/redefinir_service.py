from django.utils import timezone
from django.contrib.auth.hashers import make_password
from django.db import transaction

from api.models import RecuperacaoSenha


class RedefinirSenhaService:
    @staticmethod
    def redefinir_senha(token, nova_senha):
        try:
            recuperacao = RecuperacaoSenha.objects.select_related('usuario').get(token=token)
        except RecuperacaoSenha.DoesNotExist:
            return False, 'Token inválido.'

        if recuperacao.usado:
            return False, 'Token já utilizado.'

        expira_em = recuperacao.expira_em

        if timezone.is_naive(expira_em):
            expira_em = timezone.make_aware(
                expira_em,
                timezone.get_current_timezone()
            )

        if expira_em < timezone.now():
            return False, 'Token expirado.'

        usuario = recuperacao.usuario
        nova_senha_hash = make_password(nova_senha)

        try:
            with transaction.atomic():
                usuario.senha_hash = nova_senha_hash
                usuario.save(update_fields=['senha_hash'])

                RecuperacaoSenha.objects.filter(
                    usuario=usuario,
                    usado=False
                ).update(usado=True)
        except Exception:
            return False, 'Erro ao redefinir senha.'

        return True, 'Senha redefinida com sucesso.'