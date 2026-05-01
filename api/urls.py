from django.urls import path, include

from rest_framework import routers
from api.views import (
    UsuarioViewSet, CoordenadorViewSet, AlunoViewSet,
    SuperAdminViewSet, LoginAPIView, InscricaoViewSet,
    CoordenadorCursoViewSet, TipoAtividadeViewSet, RegraAtividadeViewSet,
    StatusSubmissaoViewSet,AtividadeComplementarViewSet,SubmissaoViewSet, CursoViewSet,
    LogAuditoriaViewSet,NotificacaoEmailViewSet, RecuperarSenhaAPIView,
    RedefinirSenhaAPIView,ExtrairDadosCertificadoView,ExtrairDadosCertificadoViewMock)

router = routers.DefaultRouter()
router.register('usuarios', UsuarioViewSet, basename='usuarios')
router.register('coordenador', CoordenadorViewSet, basename='coordenador')
router.register('aluno', AlunoViewSet, basename='aluno')
router.register('superadmin', SuperAdminViewSet, basename='superadmin' )
router.register('inscricao', InscricaoViewSet, basename='inscricao')
router.register('coordenacaoCurso', CoordenadorCursoViewSet, basename= 'coordenacaoCurso')
router.register('tipoAtividade', TipoAtividadeViewSet, basename='tipoAtividade')
router.register('regraAtividade', RegraAtividadeViewSet, basename= 'regraAtividade')
router.register('statusSubmissao', StatusSubmissaoViewSet, basename='statusSubmissao' )
router.register('atividadeComplementar', AtividadeComplementarViewSet, basename= 'AtividadeComplementar')
router.register('submissao',SubmissaoViewSet, basename= 'submissao')
router.register('curso', CursoViewSet, basename= 'curso')
router.register('auditoria', LogAuditoriaViewSet, basename='auditoria')
router.register('notificacaoEmail', NotificacaoEmailViewSet, basename='notificacaoEmail')
urlpatterns = [
    path('login/', LoginAPIView.as_view(), name='login'),
    path('redefinir-senha/', RedefinirSenhaAPIView.as_view(), name='redefinir-senha'),
    path('recuperar-senha/', RecuperarSenhaAPIView.as_view(), name='recuperar-senha'),

    # produção (Render)
    path('ocr/', ExtrairDadosCertificadoViewMock.as_view()),
    # local (troca manual)
    # path('ocr/', ExtrairDadosCertificadoViewReal.as_view()),
    path('', include(router.urls)),

]
