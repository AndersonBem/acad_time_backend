import jwt
from django.conf import settings
from rest_framework import authentication, exceptions
from api.models import Usuario

class JWTUsuarioAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.headers.get('Authorization')

        if not auth_header:
            return None
        partes = auth_header.split()

        if len(partes) != 2 or partes[0].lower() != 'bearer':
            raise exceptions.AuthenticationFailed('Header Authorization inválido.')

        token = partes[1]

        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms = [settings.JWT_ALGORITHM]
            )
        except jwt.ExpiredSignatureError:
            raise exceptions.AuthenticationFailed('Token expirado.')
        except jwt.InvalidTokenError:
            raise exceptions.AuthenticationFailed('Token inválido.')
        
        user_id = payload.get('user_id')

        if not user_id:
            raise exceptions.AuthenticationFailed('Token sem user_id.')
        try:
            usuario = Usuario.objects.get(id_usuario = user_id)
        except Usuario.DoesNotExist:
            raise exceptions.AuthenticationFailed('Usuário não encontrado.')

        return (usuario, token)