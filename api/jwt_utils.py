import jwt
from datetime import datetime, timezone
from django.conf import settings

def gerar_access_token(usuario, tipo_usuario):
    agora = datetime.now(timezone.utc)
    exp = agora + settings.JWT_ACCESS_TOKEN_LIFETIME

    payload = {
        'user_id' : usuario.id_usuario,
        'email': usuario.email,
        'tipo' : tipo_usuario,
        'iat': int(agora.timestamp()),
        'exp': int(exp.timestamp())
    }

    token = jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm= settings.JWT_ALGORITHM
    )

    return token