from rest_framework import status,viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError,AuthenticationFailed
from django.db import (connection, IntegrityError, DatabaseError,
                        InternalError, transaction)
from django.http import FileResponse



from django.core.files.storage import default_storage
import uuid 
import os
from django.contrib.auth.hashers import make_password, check_password
from django.utils import timezone

from api.models import (Usuario, Coordenador, Aluno,
                        SuperAdmin, Inscricao, CoordenacaoCurso,
                        TipoAtividade,RegraAtividade, StatusSubmissao,
                        AtividadeComplementar,  Submissao, Curso,
                        LogAuditoria, NotificacaoEmail,Certificado)

from api.serializers import (
    UsuarioSerializer, 
    CoordenadorSerializer, CoordenadorCreateSerializer, CoordenadorUpdateSerializer, 
    AlunoSerializer, AlunoCreateSerializer,AlunoUpdateSerializer,
    SuperAdminSerializer, LoginSerializer, InscricaoReadSerializer,
    InscricaoCreateSerializer, InscricaoUpdateSerializer, CoordenacaoCursoCreateSerializer,
    CoordenacaoCursoUpdateSerializer,CoordenacaoCursoReadSerializer,
    TipoAtividadeSerializer,RegraAtividadeSerializer,StatusSubmissaoSerializer,
    AtividadeComplementarSerializer, SubmissaoReadSerializer, CursoSerializer,
    SubmissaoCreateSerializer, SubmissaoUpdateSerializer,LogAuditoriaReadSerializer,
    NotificacaoEmailReadSerializer, RecuperarSenhaSerializer, RedefinirSenhaSerializer,CertificadoExtracaoSerializer)

from api.jwt_utils import gerar_access_token
from .mixins import AuditContextMixin
from api.notificacao_service import NotificacaoService
from api.recuperar_service import RecuperacaoSenhaService
from api.redefinir_service import RedefinirSenhaService
from api.utils_auditoria import set_audit_context
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

class UsuarioViewSet(viewsets.ReadOnlyModelViewSet):
    """Listando usuários, sem permitir criação, deleteção e etc, esses metodos
    vão ser usadas nas tabelas detalhadas de usuario(coordenador, aluno e SuperAdmin)"""
    permission_classes = [IsAuthenticated]
    serializer_class = UsuarioSerializer
    def get_queryset(self):
        usuario = self.request.user
        if hasattr(usuario, 'superadmin'):
            return Usuario.objects.all()
        raise PermissionDenied('Apenas superadmin pode acessar usuários.')
    
    @swagger_auto_schema(
        operation_summary="Detalhar usuário",
        operation_description="Retorna os dados de um usuário específico. Apenas superadmin pode acessar.",
        responses={
            200: UsuarioSerializer,
            401: "Não autenticado.",
            403: "Apenas superadmin pode acessar usuários.",
            404: "Usuário não encontrado.",
        },
        tags=["13 - Usuario"]
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

class CoordenadorViewSet(AuditContextMixin, viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    """Tabela especifica que herda de usuario, aqui vai permitir os metodos
    que usuarioviewset não possue"""
    queryset = Coordenador.objects.select_related('usuario').prefetch_related(
        'coordenacoes__curso',
        'telefone_set'
    )

    def _validar_superadmin(self, request):
        usuario = request.user

        if not hasattr(usuario, 'superadmin'):
            raise PermissionDenied('Apenas superadmin pode realizar esta ação.')

    """Definindo se o serializer_class vai ser de POST ou GET"""
    def get_serializer_class(self):
        if self.action == 'create':
            return CoordenadorCreateSerializer
        if self.action in ['update', 'partial_update']:
            return CoordenadorUpdateSerializer
        return CoordenadorSerializer
    
    """Quando apagar o coordenador, precisa apagar o usuario, se não ele vai manter o usuario sem ter relação com as
    tabelas filhas. Para facilitar, vou mandar ele deletar o usuario relacionado a coordenador e o banco vai apagar o 
    coordenador pelo cascade"""
    @transaction.atomic
    def destroy(self, request, *args, **kwargs):
        set_audit_context(request)
        self._validar_superadmin(request)

        """pega o objeto coordenador"""
        coordenador = self.get_object()

        """pega o usuario do coordenador"""
        usuario = coordenador.usuario
        usuario.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)

    @swagger_auto_schema(
        operation_summary="Criar coordenador",
        operation_description="""
    Cria um novo coordenador no sistema, incluindo o usuário associado.

    Regras:
    - Apenas superadmin pode criar coordenadores.
    - A criação é feita via procedure no banco de dados.
    - O email deve ser único.
    - Pode incluir telefone opcional.

    Erros possíveis:
    - Email já em uso
        """,
        request_body=CoordenadorCreateSerializer,
        responses={
            201: CoordenadorSerializer,
            400: "Dados inválidos ou email já existente.",
            401: "Não autenticado.",
            403: "Apenas superadmin pode criar coordenador.",
        },
        tags=["12 - Coordenador"]
    )

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        set_audit_context(request)
        self._validar_superadmin(request)

        """Pegando o serializer que foi definido antes e as informações que
        vieram do frontend"""
        serializer = self.get_serializer(data=request.data)
        """Valida os dados, se tiver erro, retorna 400"""
        serializer.is_valid(raise_exception=True)
        """capturando os dados de acordo com o pedido na procedure"""
        nome = serializer.validated_data['nome']
        email = serializer.validated_data['email']

        """Lógica para pegar a senha e passar ela pelo hash"""
        senha = serializer.validated_data['senha']
        senha_hash = make_password(senha)

        telefone = serializer.validated_data.get('telefone')

        """Aqui estou conecatando direto no banco e chamando a procedure"""
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    'CALL sp_cadastrar_coordenador_com_usuario(%s, %s, %s, %s)',
                    [nome, email, senha_hash, telefone]
                )
        except IntegrityError as e:
            erro = str(e)

            if 'Usuario_email_key' in erro:
                raise ValidationError("O email já está em uso.")
            raise ValidationError("Erro ao cadastrar coordenador")
        except DatabaseError as e:
            erro = str(e)

            if 'Já existe outro usuário com este email' in erro:
               raise ValidationError("Email já está em uso")

            raise ValidationError("Erro ao atualizar coordenador")

        """Capturando o objeto criado, depois chamando o serializer de coordenador
        pra deixar ele no formado correto e respondendo pro front esse json"""
        coordenador = Coordenador.objects.get(usuario__email=email)
        response_serializer = CoordenadorSerializer(coordenador)

        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(
        operation_summary="Atualizar coordenador",
        operation_description="""
    Atualiza os dados de um coordenador.

    Regras:
    - Apenas superadmin pode atualizar coordenadores.
    - Email deve continuar único.
        """,
        request_body=CoordenadorUpdateSerializer,
        responses={
            200: CoordenadorSerializer,
            400: "Dados inválidos.",
            401: "Não autenticado.",
            403: "Apenas superadmin pode atualizar coordenador.",
            404: "Coordenador não encontrado.",
        },
        tags=["12 - Coordenador"]
    )

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        set_audit_context(request)
        self._validar_superadmin(request)

        coordenador = self.get_object()

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        nome = serializer.validated_data.get('nome')
        email = serializer.validated_data.get('email')
        status_coordenador = serializer.validated_data.get('status')

        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    'CALL sp_atualizar_coordenador_com_usuario(%s, %s, %s, %s)',
                    [
                        coordenador.usuario.id_usuario,
                        nome,
                        email,
                        status_coordenador
                    ]
                )
        except IntegrityError as e:
            erro = str(e)
            if 'Usuario_email_key' in erro:
                raise ValidationError("O email já está em uso.")
            raise ValidationError("Erro ao atualizar coordenador.")
        except DatabaseError as e:
            erro = str(e)

            if 'Já existe outro usuário com este email' in erro:
                raise ValidationError("O email já está em uso.")

            raise ValidationError("Erro ao atualizar coordenador")
        
        coordenador_atualizado = Coordenador.objects.get(
            usuario__id_usuario=coordenador.usuario.id_usuario
        )

        response_serializer = CoordenadorSerializer(coordenador_atualizado)

        return Response(response_serializer.data, status=status.HTTP_200_OK)
    
    @transaction.atomic
    def partial_update(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)


class CoordenadorCursoViewSet(AuditContextMixin, viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        usuario = self.request.user

        queryset = CoordenacaoCurso.objects.select_related(
            'coordenador',
            'curso',
            'coordenador__usuario'
        ).order_by('id_coordenacao_curso')

        if hasattr(usuario, 'superadmin'):
            return queryset

        if hasattr(usuario, 'coordenador'):
            return queryset.filter(
                coordenador=usuario.coordenador,
                data_fim__isnull=True
            )

        return CoordenacaoCurso.objects.none()

    def get_serializer_class(self):
        if self.action == 'create':
            return CoordenacaoCursoCreateSerializer
        if self.action in ['update', 'partial_update']:
            return CoordenacaoCursoUpdateSerializer
        return CoordenacaoCursoReadSerializer

    def _validar_superadmin(self, request):
        usuario = request.user
        if not hasattr(usuario, 'superadmin'):
            raise PermissionDenied('Apenas superadmin pode realizar esta ação.')

    @swagger_auto_schema(
        operation_summary="Criar vínculo coordenador-curso",
        operation_description="""
    Cria um vínculo entre um coordenador e um curso.

    Regras:
    - Apenas usuários do tipo superadmin podem criar vínculos.
    - Define qual coordenador é responsável por determinado curso.
        """,
        request_body=CoordenacaoCursoCreateSerializer,
        responses={
            201: CoordenacaoCursoReadSerializer,
            400: "Dados inválidos.",
            401: "Não autenticado.",
            403: "Apenas superadmin pode criar vínculo.",
        },
        tags=["07 - Coordenacao Curso"]
    )

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        self._validar_superadmin(request)
        return super().create(request, *args, **kwargs)

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        self._validar_superadmin(request)
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Atualizar vínculo coordenador-curso",
        operation_description="""
    Atualiza um vínculo entre coordenador e curso.

    Regras:
    - Apenas superadmin pode atualizar vínculos.
    - Usado, por exemplo, para encerrar um vínculo (definir data_fim).
        """,
        request_body=CoordenacaoCursoUpdateSerializer,
        responses={
            200: CoordenacaoCursoReadSerializer,
            400: "Dados inválidos.",
            401: "Não autenticado.",
            403: "Apenas superadmin pode atualizar vínculo.",
            404: "Vínculo não encontrado.",
        },
        tags=["07 - Coordenacao Curso"]
    )

    @transaction.atomic
    def partial_update(self, request, *args, **kwargs):
        self._validar_superadmin(request)
        return super().partial_update(request, *args, **kwargs)

    @transaction.atomic
    def destroy(self, request, *args, **kwargs):
        return Response(
            {'detail': 'Exclusão de vínculo não é permitida.'},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )

class InscricaoViewSet(AuditContextMixin, viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        usuario = self.request.user

        aluno_id = self.request.query_params.get('aluno')

        if aluno_id:
            return Inscricao.objects.select_related(
                'aluno',
                'aluno__usuario',
                'curso',
                'status_matricula'
            ).filter(aluno_id=aluno_id)

        if hasattr(usuario, 'superadmin'):
            return Inscricao.objects.select_related(
                'aluno',
                'aluno__usuario',
                'curso',
                'status_matricula'
            ).all()

        if hasattr(usuario, 'coordenador'):
            return Inscricao.objects.select_related(
                'aluno',
                'aluno__usuario',
                'curso',
                'status_matricula'
            ).filter(
                curso__coordenacaocurso__coordenador=usuario.coordenador,
                curso__coordenacaocurso__data_fim__isnull=True
            )

        if hasattr(usuario, 'aluno'):
            return Inscricao.objects.select_related(
                'aluno',
                'aluno__usuario',
                'curso',
                'status_matricula'
            ).filter(aluno=usuario.aluno)

        return Inscricao.objects.none()

    def get_serializer_class(self):
        if self.action == 'create':
            return InscricaoCreateSerializer
        if self.action  in ['update', 'partial_update']:
            return InscricaoUpdateSerializer
        return InscricaoReadSerializer
    
    
    def destroy(self, request, *args, **kwargs):
        raise ValidationError("Exclusão de inscrição não é permitida.")
    def _validar_coordenador_ou_superadmin(self, request):
        usuario = request.user

        eh_coordenador = hasattr(usuario, 'coordenador')
        eh_superadmin = hasattr(usuario, 'superadmin')

        if not (eh_coordenador or eh_superadmin):
            raise PermissionDenied('Apenas coordenador ou superadmin pode realizar esta ação.')
    
    @swagger_auto_schema(
        operation_summary="Criar inscrição",
        operation_description="""
    Cria uma inscrição de aluno em um curso.

    Regras:
    - Apenas coordenador ou superadmin podem criar inscrições.
    - Coordenador só pode criar inscrição para cursos sob sua coordenação ativa.
    - Aluno não pode criar inscrição diretamente.
        """,
        request_body=InscricaoCreateSerializer,
        responses={
            201: InscricaoReadSerializer,
            400: "Dados inválidos.",
            401: "Não autenticado.",
            403: "Sem permissão para criar inscrição.",
        },
        tags=["06 - Inscricao"]
    )

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        self._validar_coordenador_ou_superadmin(request)
        return super().create(request, *args, **kwargs)

    @transaction.atomic
    def perform_create(self, serializer):
        usuario = self.request.user
        
        #Coordenador
        
        if hasattr(usuario, 'coordenador'):
            curso = serializer.validated_data.get('curso')

            vinculo = curso.coordenacaocurso_set.filter(
                coordenador= usuario.coordenador,
                data_fim__isnull=True
            ).exists()

            if not vinculo:
                raise PermissionDenied('Você não pode criar inscrição para este curso.')
            
            serializer.save()
            return
        
        # SuperAdmin

        if hasattr(usuario, 'superadmin'):
            serializer.save()
            return

        raise PermissionDenied('Sem permissão.')

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        self.get_object()
        self._validar_coordenador_ou_superadmin(request)
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Atualizar status da inscrição",
        operation_description="""
    Atualiza parcialmente uma inscrição, geralmente para alterar seu status.

    Regras:
    - Apenas coordenador ou superadmin podem atualizar inscrições.
    - Coordenador só pode atuar sobre inscrições de cursos sob sua coordenação.
    - Exclusão de inscrição não é permitida.
        """,
        request_body=InscricaoUpdateSerializer,
        responses={
            200: InscricaoReadSerializer,
            400: "Dados inválidos.",
            401: "Não autenticado.",
            403: "Sem permissão para atualizar inscrição.",
            404: "Inscrição não encontrada.",
        },
        tags=["06 - Inscricao"]
    )

    @transaction.atomic
    def partial_update(self, request, *args, **kwargs):
        self.get_object()
        self._validar_coordenador_ou_superadmin(request)
        return super().partial_update(request, *args, **kwargs)

class AlunoViewSet(AuditContextMixin, viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        usuario = self.request.user

        base_qs = Aluno.objects.select_related('usuario').prefetch_related(
            'inscricoes__curso',
            'inscricoes__status_matricula'
        )

        # superadmin

        if hasattr(usuario, 'superadmin'):
            return base_qs
        
        # coordenador

        if hasattr(usuario, 'coordenador'):
            return base_qs.filter(
                inscricoes__curso__coordenacaocurso__coordenador=usuario.coordenador,
                inscricoes__curso__coordenacaocurso__data_fim__isnull=True
            ).distinct()

        # aluno

        if hasattr(usuario, 'aluno'):
            return base_qs.filter(pk= usuario.aluno.pk)

        return Aluno.objects.none()
    
    def get_serializer_class(self):
        if self.action == 'create':
            return AlunoCreateSerializer
        if self.action in ['update', 'partial_update']:
            return AlunoUpdateSerializer
        return AlunoSerializer
    
    def _validar_apenas_superadmin(self, request):
        if not hasattr(request.user, 'superadmin'):
            raise PermissionDenied('Apenas superadmin pode realizer esta ação.')

    @transaction.atomic
    def destroy(self, request, *args, **kwargs):
        set_audit_context(request)
        self._validar_apenas_superadmin(request)
        aluno = self.get_object()

        usuario = aluno.usuario
        usuario.delete()

        return Response(status= status.HTTP_204_NO_CONTENT)
    
    @swagger_auto_schema(
        operation_summary="Criar aluno",
        operation_description="""
    Cria um novo aluno no sistema, incluindo o usuário associado.

    Regras:
    - Apenas superadmin pode criar alunos.
    - A criação é feita via procedure no banco de dados.
    - Email e matrícula devem ser únicos.

    Erros possíveis:
    - Email já em uso
    - Matrícula já em uso
        """,
        request_body=AlunoCreateSerializer,
        responses={
            201: AlunoSerializer,
            400: "Dados inválidos ou email/matrícula já existentes.",
            401: "Não autenticado.",
            403: "Apenas superadmin pode criar aluno.",
        },
        tags=["11 - Aluno"]
    )

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        set_audit_context(request)
        self._validar_apenas_superadmin(request)
        serializer = self.get_serializer(data = request.data)
        serializer.is_valid(raise_exception = True)
        nome = serializer.validated_data['nome']
        email = serializer.validated_data['email']
        senha = serializer.validated_data['senha']
        senha_hash = make_password(senha)
        matricula = serializer.validated_data['matricula']

        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    'CALL sp_cadastrar_aluno_com_usuario(%s, %s, %s, %s)',
                    [nome, email, senha_hash, matricula]
                )
        except IntegrityError as e:
            erro = str(e)

            if 'Usuario_email_key' in erro:
                raise ValidationError("Email já está em uso")

            elif 'Aluno_matricula_key' in erro:
                raise ValidationError("Matrícula já está em uso")
            raise ValidationError("Erro ao cadastrar aluno")
        except DatabaseError as e:
            erro = str(e)

            if 'Já existe outro usuário com este email' in erro:
                raise ValidationError("Email já está em uso")

            raise ValidationError("Erro ao criar aluno")
        
        aluno = Aluno.objects.get(usuario__email = email)
        response_serializer = AlunoSerializer(aluno)

        return Response(response_serializer.data, status= status.HTTP_201_CREATED)
    

    @swagger_auto_schema(
        operation_summary="Atualizar aluno",
        operation_description="""
    Atualiza os dados de um aluno e do usuário associado.

    Regras:
    - Apenas superadmin pode atualizar.
    - Email e matrícula devem continuar únicos.
        """,
        request_body=AlunoUpdateSerializer,
        responses={
            200: AlunoSerializer,
            400: "Dados inválidos ou conflito de email/matrícula.",
            401: "Não autenticado.",
            403: "Apenas superadmin pode atualizar aluno.",
            404: "Aluno não encontrado.",
        },
        tags=["11 - Aluno"]
    )

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        set_audit_context(request)
        self._validar_apenas_superadmin(request)
        aluno = self.get_object()
        serializer = self.get_serializer(data = request.data)
        serializer.is_valid(raise_exception = True)

        nome = serializer.validated_data.get('nome')
        email = serializer.validated_data.get('email')
        matricula = serializer.validated_data.get('matricula')

        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    'CALL sp_atualizar_aluno_com_usuario(%s, %s, %s, %s)',
                    [
                        aluno.usuario.id_usuario,
                        nome,
                        email,
                        matricula
                    ]
                )
        except IntegrityError as e:
            erro = str(e)

            if 'Usuario_email_key' in erro:
                raise ValidationError("Email já está em uso")

            elif 'Aluno_matricula_key' in erro:
                raise ValidationError("Matrícula já está em uso")
            raise ValidationError("Erro ao atualizar aluno")
        except DatabaseError as e:
            erro = str(e)

            if 'Já existe outro usuário com este email' in erro:
                raise ValidationError("Email já está em uso")

            raise ValidationError("Erro ao atualizar aluno")

        aluno_atualizado = Aluno.objects.get(
            usuario__id_usuario = aluno.usuario.id_usuario
        )

        response_serializer = AlunoSerializer(aluno_atualizado)
        return Response(response_serializer.data, status= status.HTTP_200_OK)
    
    @transaction.atomic
    def partial_update(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

class SuperAdminViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = SuperAdminSerializer

    def get_queryset(self):
        usuario = self.request.user

        if hasattr(usuario, 'superadmin'):
            return SuperAdmin.objects.all()

        raise PermissionDenied('Apenas superadmin pode acessar este endpoint.')
    
    @swagger_auto_schema(
        operation_summary="Detalhar superadmin",
        operation_description="Retorna os dados de um superadmin específico.",
        responses={
            200: SuperAdminSerializer,
            401: "Não autenticado.",
            403: "Apenas superadmin pode acessar este endpoint.",
            404: "Superadmin não encontrado.",
        },
        tags=["14 - SuperAdmin"]
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

class LoginAPIView(APIView):
    permission_classes = [AllowAny]
    
    @swagger_auto_schema(
        operation_summary="Login do usuário",
        operation_description="""
                            Autentica o usuário e retorna um token JWT.

                            Tipos de usuário possíveis:
                            - aluno
                            - coordenador
                            - superadmin

                            Após o login, utilize o token no header:

                            Authorization: Bearer <token>
                                """,
        request_body=LoginSerializer,
        responses={
            200: openapi.Response(
                description="Login realizado com sucesso.",
                examples={
                    "application/json": {
                        "mensagem": "Login realizado com sucesso.",
                        "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                        "usuario": {
                            "id": 1,
                            "nome": "João Silva",
                            "email": "joao@email.com",
                            "tipo": "aluno"
                        }
                    }
                }
            ),
            400: "Dados inválidos.",
            401: "Email ou senha inválidos."
        },
        tags=["01 - Login"]
    )

    def post(self, request):
        serializer = LoginSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status= status.HTTP_400_BAD_REQUEST
            )
        email = serializer.validated_data['email']
        senha = serializer.validated_data['senha']

        try:
            usuario = Usuario.objects.get(email = email)
        except Usuario.DoesNotExist:
            raise AuthenticationFailed("Email ou senha inválidos")
        
        if not check_password(senha, usuario.senha_hash):
            raise AuthenticationFailed("Email ou senha inválidos")
            
        tipo_usuario = self.descobrir_tipo_usuario(usuario)
        access_token = gerar_access_token(usuario, tipo_usuario)

        return Response(
            {
                'mensagem': 'Login realizado com sucesso.',
                'access': access_token,
                'usuario': {
                    'id': usuario.id_usuario,
                    'nome': usuario.nome,
                    'email': usuario.email,
                    'tipo': tipo_usuario,
                }
            },
            status=status.HTTP_200_OK
        )
    
    def descobrir_tipo_usuario(self, usuario):
        if hasattr(usuario, 'aluno'):
            return 'aluno'
        
        if hasattr(usuario, 'coordenador'):
            return 'coordenador'

        if hasattr(usuario, 'superadmin'):
            return 'superadmin'

        return 'usuario'

class TipoAtividadeViewSet(AuditContextMixin, viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = TipoAtividade.objects.all().order_by('nome')
    serializer_class = TipoAtividadeSerializer

    def _validar_apenas_superadmin(self, request):
        if not hasattr(request.user, 'superadmin'):
            raise PermissionDenied('Apenas superadmin pode realizar esta ação.')

    @swagger_auto_schema(
        operation_summary="Criar tipo de atividade",
        operation_description="""
    Cria um novo tipo de atividade complementar.

    Exemplos:
    - Curso
    - Palestra
    - Evento

    Regras:
    - Apenas usuários do tipo superadmin podem criar tipos de atividade.
        """,
        request_body=TipoAtividadeSerializer,
        responses={
            201: TipoAtividadeSerializer,
            400: "Dados inválidos.",
            401: "Não autenticado.",
            403: "Apenas superadmin pode criar tipo de atividade.",
        },
        tags=["09 - Tipo Atividade"]
    )

    def create(self, request, *args, **kwargs):
        self._validar_apenas_superadmin(request)
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        self._validar_apenas_superadmin(request)
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Atualizar tipo de atividade",
        operation_description="""
    Atualiza um tipo de atividade complementar.

    Regras:
    - Apenas superadmin pode atualizar.
        """,
        request_body=TipoAtividadeSerializer,
        responses={
            200: TipoAtividadeSerializer,
            400: "Dados inválidos.",
            401: "Não autenticado.",
            403: "Apenas superadmin pode atualizar tipo de atividade.",
            404: "Tipo de atividade não encontrado.",
        },
        tags=["09 - Tipo Atividade"]
    )

    def partial_update(self, request, *args, **kwargs):
        self._validar_apenas_superadmin(request)
        return super().partial_update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        raise PermissionDenied("Exclusão de tipo de atividade não é permitida.")
    
class RegraAtividadeViewSet(AuditContextMixin, viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        queryset = RegraAtividade.objects.select_related(
            'curso',
            'tipo_atividade'
        ).order_by('curso')

        curso_id = self.request.query_params.get('curso')

        if curso_id:
            queryset = queryset.filter(curso_id=curso_id)

        usuario = self.request.user

        if hasattr(usuario, 'superadmin'):
            return queryset

        if hasattr(usuario, 'coordenador'):
            return queryset.filter(
                curso__coordenacaocurso__coordenador=usuario.coordenador,
                curso__coordenacaocurso__data_fim__isnull=True
            ).distinct()

        return RegraAtividade.objects.none()
    
    serializer_class = RegraAtividadeSerializer

    def _validar_apenas_superadmin(self, request):
        if not hasattr(request.user, 'superadmin'):
            raise PermissionDenied('Apenas superadmin pode realizar esta ação.')

    @swagger_auto_schema(
        operation_summary="Criar regra de atividade",
        operation_description="""
    Define uma regra de atividade para um curso.

    Exemplo de uso:
    - Limitar carga horária máxima por tipo de atividade
    - Definir se exige comprovante

    Regras:
    - Apenas usuários do tipo superadmin podem criar regras de atividade.
    - Cada regra está vinculada a um curso e a um tipo de atividade.
        """,
        request_body=RegraAtividadeSerializer,
        responses={
            201: RegraAtividadeSerializer,
            400: "Dados inválidos.",
            401: "Não autenticado.",
            403: "Apenas superadmin pode criar regra de atividade.",
        },
        tags=["10 - Regra Atividade"]
    )

    def create(self, request, *args, **kwargs):
        self._validar_apenas_superadmin(request)
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        self._validar_apenas_superadmin(request)
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Atualizar regra de atividade",
        operation_description="""
    Atualiza uma regra de atividade vinculada a um curso.

    Regras:
    - Apenas superadmin pode atualizar regras de atividade.
        """,
        request_body=RegraAtividadeSerializer,
        responses={
            200: RegraAtividadeSerializer,
            400: "Dados inválidos.",
            401: "Não autenticado.",
            403: "Apenas superadmin pode atualizar regra de atividade.",
            404: "Regra não encontrada.",
        },
        tags=["10 - Regra Atividade"]
    )

    def partial_update(self, request, *args, **kwargs):
        self._validar_apenas_superadmin(request)
        return super().partial_update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        raise PermissionDenied("Exclusão de regra de atividade não é permitida.")
        
class StatusSubmissaoViewSet(AuditContextMixin, viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = StatusSubmissao.objects.all().order_by('nome_status')
    serializer_class = StatusSubmissaoSerializer

    @swagger_auto_schema(
        operation_summary="Listar status de submissão",
        operation_description="""
Retorna todos os status possíveis de uma submissão.

Exemplos:
- PENDENTE
- APROVADA
- REPROVADA

Utilizado para definir ou exibir o status de uma submissão.
        """,
        responses={
            200: StatusSubmissaoSerializer(many=True),
            401: "Não autenticado."
        },
        tags=["05 - Status Submissao"]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

class AtividadeComplementarViewSet(AuditContextMixin, viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = AtividadeComplementarSerializer

    def get_queryset(self):
        usuario = self.request.user
        queryset = AtividadeComplementar.objects.all().order_by('id_atividade_complementar')

        if hasattr(usuario, 'superadmin'):
            return queryset

        if hasattr(usuario, 'coordenador'):
            return queryset.filter(
                submissao__curso__coordenacaocurso__coordenador=usuario.coordenador,
                submissao__curso__coordenacaocurso__data_fim__isnull=True
            ).distinct()

        if hasattr(usuario, 'aluno'):
            return queryset.filter(
                submissao__aluno=usuario.aluno
            ).distinct()

        return queryset.none()

    @swagger_auto_schema(
        operation_summary="Listar atividades complementares",
        operation_description="""
Lista as atividades complementares visíveis para o usuário autenticado.

Regras:
- Superadmin visualiza todas.
- Coordenador visualiza atividades vinculadas às submissões dos cursos sob sua coordenação ativa.
- Aluno visualiza atividades vinculadas às suas próprias submissões.
        """,
        responses={
            200: AtividadeComplementarSerializer(many=True),
            401: "Não autenticado.",
        },
        tags=["04 - Atividade Complementar"]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Criar atividade complementar",
        operation_description="""
    Cria uma nova atividade complementar.

    Regras:
    - Apenas alunos autenticados podem criar.
    - Coordenadores, superadmins e outros perfis não podem criar por este endpoint.
        """,
        request_body=AtividadeComplementarSerializer,
        responses={
            201: AtividadeComplementarSerializer,
            400: "Dados inválidos.",
            401: "Não autenticado.",
            403: "Apenas aluno pode criar atividade complementar.",
        },
        tags=["04 - Atividade Complementar"]
    )

    def create(self, request, *args, **kwargs):
        if not hasattr(request.user, 'aluno'):
            raise PermissionDenied('Apenas aluno pode criar atividade complementar.')
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        raise PermissionDenied('Edição de atividade complementar não é permitida.')

    def partial_update(self, request, *args, **kwargs):
        raise PermissionDenied('Edição de atividade complementar não é permitida.')

    def destroy(self, request, *args, **kwargs):
        raise PermissionDenied('Exclusão de atividade complementar não é permitida.')

class CursoViewSet(AuditContextMixin, viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = Curso.objects.all()
    serializer_class = CursoSerializer

    def _validar_apenas_superadmin(self, request):
        if not hasattr(request.user, 'superadmin'):
            raise PermissionDenied('Apenas superadmin pode realizar esta ação.')

    @swagger_auto_schema(
        operation_summary="Criar curso",
        operation_description="""
    Cria um novo curso no sistema.

    Regras:
    - Apenas usuários do tipo superadmin podem criar cursos.
        """,
        request_body=CursoSerializer,
        responses={
            201: CursoSerializer,
            400: "Dados inválidos.",
            401: "Não autenticado.",
            403: "Apenas superadmin pode criar cursos.",
        },
        tags=["08 - Curso"]
    )

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        self._validar_apenas_superadmin(request)
        return super().create(request, *args, **kwargs)

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        self._validar_apenas_superadmin(request)
        return super().update(request, *args, **kwargs)
      
    @transaction.atomic
    def partial_update(self, request, *args, **kwargs):
        self._validar_apenas_superadmin(request)
        return super().partial_update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        return Response(
            {'erro': 'Exclusão de curso não é permitida.'},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )


class SubmissaoViewSet(AuditContextMixin, viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    def get_queryset(self):
        usuario = self.request.user

        queryset = Submissao.objects.select_related(
            'aluno',
            'aluno__usuario',
            'curso',
            'atividade_complementar',
            'status_submissao',
            'certificado',
            'coordenador',
            'coordenador__usuario'
        )

        if hasattr(usuario, 'aluno'):
            return queryset.filter(aluno=usuario.aluno)

        if hasattr(usuario, 'coordenador'):
            return queryset.filter(
                curso__coordenacaocurso__coordenador=usuario.coordenador,
                curso__coordenacaocurso__data_fim__isnull=True
            ).distinct()

        if hasattr(usuario, 'superadmin'):
            return queryset

        return queryset.none()
    
    serializer_class = SubmissaoReadSerializer
    
    def get_serializer_class(self):
        if self.action == 'create':
            return SubmissaoCreateSerializer
        if self.action in ['update', 'partial_update']:
            return SubmissaoUpdateSerializer
        return SubmissaoReadSerializer
    
    @swagger_auto_schema(
        operation_summary="Criar submissão",
        operation_description="""
                            Cria uma nova submissão de atividade complementar.

                            Este endpoint recebe dados em multipart/form-data e exige o envio
                            do arquivo do certificado no campo certificado_arquivo.

                            Regras:
                            - Apenas alunos autenticados podem criar submissões.
                            - O aluno precisa possuir inscrição ativa no curso informado.
                            - O curso precisa possuir coordenador ativo.
                            - O arquivo deve estar nos formatos: PDF, JPG, JPEG ou PNG.
                            - A submissão é criada automaticamente com status PENDENTE.
                                    """,
        manual_parameters=[
            openapi.Parameter(
                'curso',
                openapi.IN_FORM,
                description='ID do curso da submissão.',
                type=openapi.TYPE_INTEGER,
                required=True
            ),
            openapi.Parameter(
                'atividade_complementar',
                openapi.IN_FORM,
                description='ID da atividade complementar.',
                type=openapi.TYPE_INTEGER,
                required=True
            ),
            openapi.Parameter(
                'certificado_arquivo',
                openapi.IN_FORM,
                description='Arquivo do certificado (.pdf, .jpg, .jpeg, .png).',
                type=openapi.TYPE_FILE,
                required=True
            ),
        ],
        responses={
            201: openapi.Response(
                description="Submissão criada com sucesso.",
                schema=SubmissaoReadSerializer
            ),
            400: "Dados inválidos ou regra de negócio não atendida.",
            401: "Não autenticado.",
            403: "Sem permissão.",
        },

        tags=["02 - Submissao"]
    )

    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)



    @transaction.atomic
    def perform_create(self, serializer):
        usuario = self.request.user


        eh_aluno = hasattr(usuario, 'aluno')

        if not eh_aluno:
            raise PermissionDenied('Apenas alunos podem criar submissões.')

        
        aluno = usuario.aluno
        curso = serializer.validated_data.get('curso')
        arquivo =  serializer.validated_data.pop('certificado_arquivo', None)
       

        possui_inscricao_ativa = Inscricao.objects.filter(
            aluno = aluno,
            curso = curso,
            status_matricula_id =1
        ).exists()

        if not possui_inscricao_ativa:
            raise ValidationError('O aluno não possui inscrição ativa nesse curso.')
        
        if not arquivo:
            raise ValidationError('O arquivo de certificado é obrigatório.')
        
        extensao = os.path.splitext(arquivo.name)[1].lower()
        extensoes_permitidas = ['.pdf', '.jpg', '.jpeg', '.png']
        nome_unico = f"{uuid.uuid4()}{extensao}"

        if extensao not in extensoes_permitidas:
            raise ValidationError({
            'certificado_arquivo': 'Formato inválido. Envie PDF, JPG, JPEG ou PNG.'
        })
        caminho_arquivo = default_storage.save(f'certificados/{nome_unico}', arquivo)


        status_pendente = StatusSubmissao.objects.get(nome_status = 'PENDENTE')   

        certificado = Certificado.objects.create(
             nome_arquivo=nome_unico,
             url_arquivo=default_storage.url(caminho_arquivo),
             data_upload=timezone.now().date()
        ) 
        coordenacao_ativa = CoordenacaoCurso.objects.filter(
            curso=curso,
            data_fim__isnull=True
        ).first()

        if not coordenacao_ativa:
            raise ValidationError('O curso informado não possui coordenador ativo.')

          

        submissao = serializer.save(
            aluno=aluno,
            data_envio=timezone.now().date(),
            status_submissao=status_pendente,
            observacao_coordenador=None,
            certificado=certificado,
            coordenador=coordenacao_ativa.coordenador
        )

        try:
            NotificacaoService.notificar_submissao_criada(submissao)
        except Exception as e:
            print(f'Erro ao enviar notificação de submissão criada: {e}')

    @transaction.atomic
    def perform_update(self, serializer):
        usuario = self.request.user
        submissao = self.get_object()
        status_anterior = submissao.status_submissao.nome_status

        eh_aluno = hasattr(usuario, 'aluno')
        eh_coordenador = hasattr(usuario, 'coordenador')
        eh_superadmin = hasattr(usuario, 'superadmin')

        if eh_aluno:
            raise PermissionDenied('Aluno não pode alterar submissões.')
        if eh_coordenador:
            vinculo_ativo = CoordenacaoCurso.objects.filter(
                coordenador=usuario.coordenador,
                curso=submissao.curso,
                data_fim__isnull=True
            ).exists()

            if not vinculo_ativo:
                raise PermissionDenied("Você não pode avaliar submissões deste curso.")
            
            try:
                with transaction.atomic():
                    serializer.save(coordenador=usuario.coordenador)
                submissao.refresh_from_db()
                status_novo = submissao.status_submissao.nome_status

                if status_anterior != status_novo:
                    try:
                        if status_novo == 'APROVADA':
                            NotificacaoService.notificar_submissao_aprovada(submissao)
                        elif status_novo == 'REPROVADA':
                            NotificacaoService.notificar_submissao_reprovada(submissao)
                    except Exception as e:
                        print(f'Erro ao enviar notificação de atualização da submissão: {e}')
                
            except InternalError as e:
                raise ValidationError({'detail': str(e)})
            return
        
        if eh_superadmin:
            try:
                with transaction.atomic():
                    serializer.save()
                submissao.refresh_from_db()
                status_novo = submissao.status_submissao.nome_status

                if status_anterior != status_novo:
                    try:
                        if status_novo == 'APROVADA':
                            NotificacaoService.notificar_submissao_aprovada(submissao)
                        elif status_novo == 'REPROVADA':
                            NotificacaoService.notificar_submissao_reprovada(submissao)
                    except Exception as e:
                        print(f'Erro ao enviar notificação de atualização da submissão: {e}')
            except InternalError as e:
                raise ValidationError({'detail': str(e)})
            return
        
        raise PermissionDenied("Usuário sem permissão para atualizar submissão.")

    @transaction.atomic
    def destroy(self, request, *args, **kwargs):
        set_audit_context(request)
        raise PermissionDenied('Exclusão de submissão não é permitida. Utilize a alteração de status.')
    
    @action(detail=True, methods=['get'], url_path='baixar-certificado')
    def baixar_certificado(self, request, pk=None):
        submissao = self.get_object()
        certificado = submissao.certificado

        if not certificado:
            raise ValidationError("Esta submissão não possui certificado.")

        caminho_arquivo = f"certificados/{certificado.nome_arquivo}"

        try:
            arquivo = default_storage.open(caminho_arquivo, "rb")
        except Exception:
            raise ValidationError("Arquivo do certificado não encontrado no storage.")

        return FileResponse(
            arquivo,
            as_attachment=True,
            filename=certificado.nome_arquivo
        )
    
class LogAuditoriaViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = LogAuditoriaReadSerializer
    
    def _validar_superadmin(self, request):
        usuario = request.user
        
        if not hasattr(usuario, 'superadmin'):
            raise PermissionDenied('Apenas superadmin pode realizar esta ação.')
    def get_queryset(self):
        self._validar_superadmin(self.request)

        return LogAuditoria.objects.select_related(
            'usuario',
            'tipo_acao'
        ).order_by('-data_hora')
    
    @swagger_auto_schema(
        operation_summary="Listar logs de auditoria",
        operation_description="""
    Retorna os registros de auditoria do sistema.

    Inclui informações como:
    - Usuário que realizou a ação
    - Tipo de ação
    - Data e hora

    Regras:
    - Apenas superadmin pode acessar.
    - Endpoint somente leitura.
        """,
        responses={
            200: LogAuditoriaReadSerializer(many=True),
            401: "Não autenticado.",
            403: "Apenas superadmin pode acessar logs de auditoria.",
        },
        tags=["17 - Log Auditoria"]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

class NotificacaoEmailViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NotificacaoEmailReadSerializer

    def _validar_superadmin(self, request):
        usuario = request.user
        if not hasattr(usuario, 'superadmin'):
            raise PermissionDenied('Apenas superadmin pode realizar esta ação.')

    def get_queryset(self):
        self._validar_superadmin(self.request)

        return NotificacaoEmail.objects.order_by('-data', '-id_notificacao_email')
    
    @swagger_auto_schema(
        operation_summary="Listar notificações de e-mail",
        operation_description="""
    Retorna o histórico de notificações de e-mail enviadas pelo sistema.

    Regras:
    - Apenas superadmin pode acessar.
    - Endpoint somente leitura.
        """,
        responses={
            200: NotificacaoEmailReadSerializer(many=True),
            401: "Não autenticado.",
            403: "Apenas superadmin pode acessar notificações.",
        },
        tags=["18 - Notificacao Email"]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
class RecuperarSenhaAPIView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_summary="Solicitar recuperação de senha",
        operation_description="""
    Solicita a recuperação de senha para um usuário.

    Fluxo:
    - O usuário informa o e-mail.
    - Se o e-mail existir, um link de redefinição é enviado.
    - A resposta é sempre genérica por segurança.

    Observação:
    - Não informa se o e-mail existe ou não no sistema.
        """,
        request_body=RecuperarSenhaSerializer,
        responses={
            200: openapi.Response(
                description="Solicitação processada com sucesso.",
                examples={
                    "application/json": {
                        "mensagem": "Se o e-mail existir, o link de recuperação foi enviado."
                    }
                }
            ),
            400: "Dados inválidos."
        },
        tags=["15 - Recuperar Senha"]
    )


    def post(self, request):
        serializer = RecuperarSenhaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']

        try:
            RecuperacaoSenhaService.solicitar_recuperacao(email)
        except Exception as e:
            print(f'Erro ao solicitar recuperação de senha: {e}')

        return Response(
            {'mensagem': 'Se o e-mail existir, o link de recuperação foi enviado.'},
            status=status.HTTP_200_OK
        )
    
class RedefinirSenhaAPIView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_summary="Redefinir senha",
        operation_description="""
    Redefine a senha do usuário a partir de um token de recuperação.

    Regras:
    - O token deve ser válido.
    - O token pode expirar.
    - A nova senha deve atender às regras de validação.

    Fluxo:
    - Usuário recebe link com token.
    - Envia token + nova senha.
    - Senha é atualizada.
        """,
        request_body=RedefinirSenhaSerializer,
        responses={
            200: openapi.Response(
                description="Senha redefinida com sucesso.",
                examples={
                    "application/json": {
                        "mensagem": "Senha redefinida com sucesso."
                    }
                }
            ),
            400: "Token inválido ou dados incorretos."
        },
        tags=["16 - Redefinir Senha"]
    )
    
    def post(self, request):
        serializer = RedefinirSenhaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        token = serializer.validated_data['token']
        nova_senha = serializer.validated_data['nova_senha']

        sucesso, mensagem = RedefinirSenhaService.redefinir_senha(token, nova_senha)

        if not sucesso:
            raise ValidationError(mensagem)

        return Response(
            {'mensagem': mensagem},
            status=status.HTTP_200_OK
        )


class ExtrairDadosCertificadoView(APIView):
    parser_classes = [MultiPartParser, FormParser]

    @swagger_auto_schema(
        operation_summary="Extrair dados do certificado",
        operation_description="""
Extrai informações de um certificado enviado pelo usuário.

Este endpoint simula o botão "Extrair dados" da tela de submissão.

Ele não salva a submissão e não grava dados no banco. Apenas lê o arquivo
e retorna os dados identificados para que o usuário possa revisar antes de salvar.

Formatos aceitos:
- PDF
- PNG
- JPG
- JPEG
        """,
        manual_parameters=[
            openapi.Parameter(
                "certificado_arquivo",
                openapi.IN_FORM,
                description="Arquivo do certificado para extração OCR.",
                type=openapi.TYPE_FILE,
                required=True
            )
        ],
        responses={
            200: openapi.Response(
                description="Resultado da extração OCR.",
                examples={
                    "application/json": {
                        "sucesso": True,
                        "dados_extraidos": {
                            "carga_horaria": "40",
                            "data_certificado": "2026-04-24",
                            "curso": "Curso de Python",
                            "instituicao": "Senac",
                            "texto_extraido": "Texto completo extraído do certificado..."
                        }
                    }
                }
            ),
            400: "Arquivo inválido ou não enviado.",
        },
        tags=["03 - OCR Certificado"]
    )
    def post(self, request):
        from .services.ocr_service import CertificadoExtracaoService
        
        serializer = CertificadoExtracaoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        arquivo = serializer.validated_data["certificado_arquivo"]

        try:
            texto = CertificadoExtracaoService.extrair_texto_arquivo(arquivo)
            dados = CertificadoExtracaoService.extrair_dados(texto)

            return Response({
                "sucesso": True,
                "dados_extraidos": dados
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "sucesso": False,
                "dados_extraidos": {
                    "carga_horaria": "",
                    "data_certificado": "",
                    "curso": "",
                    "instituicao": "",
                    "texto_extraido": ""
                },
                "erro": f"Não foi possível extrair os dados do certificado: {str(e)}"
            }, status=status.HTTP_200_OK)
        

class ExtrairDadosCertificadoViewMock(APIView):
    parser_classes = [MultiPartParser, FormParser]

    @swagger_auto_schema(
        operation_summary="Extrair dados do certificado (Mock)",
        operation_description="Versão mockada para ambiente de produção.",
        manual_parameters=[
            openapi.Parameter(
                "certificado_arquivo",
                openapi.IN_FORM,
                description="Arquivo do certificado.",
                type=openapi.TYPE_FILE,
                required=True
            )
        ],
        responses={
            200: openapi.Response(
                description="Resultado mockado.",
                examples={
                    "application/json": {
                        "sucesso": True,
                        "dados_extraidos": {
                            "carga_horaria": "40",
                            "data_certificado": "2026-04-24",
                            "curso": "Curso de Python",
                            "instituicao": "Senac",
                            "texto_extraido": "Texto mockado para demonstração."
                        }
                    }
                }
            )
        },
        tags=["03 - OCR Certificado"]
    )
    def post(self, request):
        return Response({
            "sucesso": True,
            "dados_extraidos": {
                "carga_horaria": "40",
                "data_certificado": "2026-04-24",
                "curso": "Curso de Python",
                "instituicao": "Senac",
                "texto_extraido": "Texto mockado para demonstração."
            }
        })
