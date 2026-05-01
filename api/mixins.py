from django.db import transaction
from .utils_auditoria import set_audit_context


class AuditContextMixin:
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        set_audit_context(request)
        return super().create(request, *args, **kwargs)

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        set_audit_context(request)
        return super().update(request, *args, **kwargs)

    @transaction.atomic
    def partial_update(self, request, *args, **kwargs):
        set_audit_context(request)
        return super().partial_update(request, *args, **kwargs)

    @transaction.atomic
    def destroy(self, request, *args, **kwargs):
        set_audit_context(request)
        return super().destroy(request, *args, **kwargs)