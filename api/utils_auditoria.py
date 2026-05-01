from django.db import connection


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()

    return request.META.get('REMOTE_ADDR')


def set_audit_context(request):
    usuario_id = getattr(request.user, 'id_usuario', None)
    ip = get_client_ip(request)

    with connection.cursor() as cursor:
        if usuario_id is not None:
            cursor.execute("SET LOCAL app.usuario_id = %s;", [str(usuario_id)])
        if ip:
            cursor.execute("SET LOCAL app.ip_origem = %s;", [ip])