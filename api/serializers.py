from rest_framework import serializers
from datetime import date
from api.models import (Usuario, Coordenador, Aluno, 
                        SuperAdmin, CoordenacaoCurso, Inscricao,
                        TipoAtividade, RegraAtividade,StatusSubmissao,
                        AtividadeComplementar,Submissao, Curso,
                        LogAuditoria, NotificacaoEmail)

"""Serializer geral para get"""
class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = '__all__'

"""Serializer apenas para leitura das informações"""
class InscricaoReadSerializer(serializers.ModelSerializer):
    nome_curso = serializers.ReadOnlyField(source = 'curso.nome')
    nome_aluno = serializers.ReadOnlyField(source = 'aluno.usuario.nome')
    numero_matricula = serializers.ReadOnlyField(source = 'aluno.matricula')
    status_matricula = serializers.ReadOnlyField(source = 'status_matricula.nome')
    
    class Meta:
        model = Inscricao
        fields = ['id_inscricao', 'nome_curso', 'nome_aluno','numero_matricula' ,'data_inscricao','status_matricula']
"""Serializer de criação da inscricão"""
class InscricaoCreateSerializer(serializers.ModelSerializer):
    class Meta: 
        model = Inscricao
        fields = ['aluno', 'curso', 'status_matricula']

    def create(self, validated_data):
        validated_data['data_inscricao'] = date.today()
        return super().create(validated_data)
    
    def validate(self, attrs):
        aluno = attrs.get('aluno')
        curso = attrs.get('curso')

        if Inscricao.objects.filter(aluno = aluno, curso = curso).exists():
            raise serializers.ValidationError('Este aluno já está vinculado a este curso')

        return attrs
    
"""Serializer de update, apenas do status"""
class InscricaoUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Inscricao
        fields = ['status_matricula']


"""Serializer apenas para leitura das informações"""
class CoordenacaoCursoReadSerializer(serializers.ModelSerializer):
    nome_curso = serializers.ReadOnlyField(source = 'curso.nome')
    nome_coordenador = serializers.ReadOnlyField(source = 'coordenador.usuario.nome')
    status = serializers.SerializerMethodField()
    class Meta:
        model = CoordenacaoCurso
        fields = ['id_coordenacao_curso','curso', 'nome_curso','coordenador', 'nome_coordenador', 'data_inicio', 'data_fim', 'status']

    def get_status(self, obj):
        if obj.data_fim:
            return 'encerrado'
        return 'ativo'
    
"""Serializer apenas criação do vinculo coordenador curso"""
class CoordenacaoCursoCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CoordenacaoCurso
        fields = ['curso', 'coordenador']

    def validate(self, attrs):
        coordenador = attrs.get('coordenador')
        curso = attrs.get('curso')

        if CoordenacaoCurso.objects.filter(
                                            coordenador=coordenador,
                                            curso=curso,
                                            data_fim__isnull=True
                                        ).exists():
            raise serializers.ValidationError('Este coordenador já está vinculado a este curso')

        return attrs
    
    def create(self, validated_data):
        validated_data['data_inicio'] = date.today()
        return super().create(validated_data)

"""Serializer apenas para encerramento do vinculo coordenador curso"""
class CoordenacaoCursoUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CoordenacaoCurso
        fields = ['data_fim']
    
    def validate_data_fim(self, value):
        if value is None:
            raise serializers.ValidationError('Informe uma data_fim para encerrar o vínculo.')
        if self.instance and value and value< self.instance.data_inicio:
            raise serializers.ValidationError('A data_fim não pode ser anterior à data_inicio.')
        return value

class CoordenacaoCursoResumoSerializer(serializers.ModelSerializer):
    curso = serializers.ReadOnlyField(source = 'curso.nome')
    class Meta:
        model = CoordenacaoCurso
        fields = ['curso']

class CoordenadorSerializer(serializers.ModelSerializer):

    id = serializers.ReadOnlyField(source = 'usuario.id_usuario')
    nome = serializers.ReadOnlyField(source = 'usuario.nome')
    email = serializers.ReadOnlyField(source = 'usuario.email')
    telefone = serializers.SerializerMethodField()
    cursos = CoordenacaoCursoResumoSerializer(
        source = 'coordenacoes',
        many = True,
        read_only = True
    )

    class Meta:
        model = Coordenador
        fields = ['id','nome', 'email', 'status', 'telefone', 'cursos']

    def get_telefone(self, obj):
        telefone = obj.telefone_set.first()
        return telefone.numero if telefone else None

"""Serializer para post, precisa por usar procedure para salvar"""
class CoordenadorCreateSerializer(serializers.Serializer):
    """criação de coordenador usando a procedure"""
    nome = serializers.CharField(max_length= 150)
    email = serializers.EmailField(max_length = 150)
    senha = serializers.CharField(write_only = True)
    telefone= serializers.CharField(max_length=20, required = False, allow_null = True, allow_blank = True)

"""Serializer para edição, precisa por usar procedure para salvar"""

class CoordenadorUpdateSerializer(serializers.Serializer):
    nome = serializers.CharField(max_length= 150, required = False)
    email = serializers.EmailField(max_length= 150, required = False)
    status = serializers.BooleanField(required=False)

    def validate(self, attrs):
        if not attrs:
            raise serializers.ValidationError(
                'Envie pelo menos um campo para atualização'
            )
        return attrs

class InscricaoResumoSerializer(serializers.ModelSerializer):
    curso = serializers.ReadOnlyField(source ='curso.nome')
    status = serializers.ReadOnlyField(source = 'status_matricula.nome')

    class Meta:
        model = Inscricao
        fields = ['curso', 'status']

class AlunoSerializer(serializers.ModelSerializer):

    id = serializers.ReadOnlyField(source = 'usuario.id_usuario')
    nome = serializers.ReadOnlyField(source = 'usuario.nome')
    email = serializers.ReadOnlyField(source = 'usuario.email')
    cursos = InscricaoResumoSerializer(
        source = 'inscricoes',
        many = True,
        read_only = True
    )

    class Meta:
        model = Aluno
        fields = ['id','nome', 'email', 'total_horas', 'matricula', 'cursos']

"""Serializer para post, precisa por usar procedure para salvar"""
class AlunoCreateSerializer(serializers.Serializer):
    """criação de coordenador usando a procedure"""
    nome = serializers.CharField(max_length= 150)
    email = serializers.EmailField(max_length = 150)
    senha = serializers.CharField(write_only = True)
    matricula = serializers.CharField(max_length = 30)

"""Serializer para edição, precisa por usar procedure para salvar"""

class AlunoUpdateSerializer(serializers.Serializer):
    nome = serializers.CharField(max_length= 150, required = False)
    email = serializers.EmailField(max_length= 150, required = False)
    matricula = serializers.CharField(max_length = 30, required = False)

    def validate(self, attrs):
        if not attrs:
            raise serializers.ValidationError(
                'Envie pelo menos um campo para atualização'
            )
        return attrs

class SuperAdminSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source = 'usuario.id_usuario')
    nome = serializers.ReadOnlyField(source = 'usuario.nome')
    email = serializers.ReadOnlyField(source = 'usuario.email')
    
    class Meta:
        model= SuperAdmin
        fields = ['id','nome', 'email']

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    senha = serializers.CharField(write_only = True)

class CursoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Curso
        fields = '__all__'

class TipoAtividadeSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoAtividade
        fields = '__all__'

class RegraAtividadeSerializer(serializers.ModelSerializer):
    tipo_atividade_nome = serializers.ReadOnlyField(source= 'tipo_atividade.nome')
    curso_nome = serializers.ReadOnlyField(source= 'curso.nome')

    class Meta:
        model = RegraAtividade
        fields = [
                    'id',
                    'tipo_atividade',
                    'tipo_atividade_nome',
                    'curso',
                    'curso_nome',
                    'limite_horas',
                    'exige_comprovante'
                ]
    
    def validate(self, attrs):
        tipo_atividade = attrs.get('tipo_atividade', self.instance.tipo_atividade if self.instance else None)
        curso = attrs.get('curso', self.instance.curso if self.instance else None)

        query = RegraAtividade.objects.filter(
            tipo_atividade = tipo_atividade,
            curso = curso
        )
        if self.instance:
            query = query.exclude(id= self.instance.id)

        if query.exists():
            raise serializers.ValidationError('Esse curso já possui uma regra de atividade.')
        return attrs
    

class StatusSubmissaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = StatusSubmissao
        fields = '__all__'

class AtividadeComplementarSerializer(serializers.ModelSerializer):
    tipo_atividade_nome = serializers.ReadOnlyField(source ='tipo_atividade.nome')
    
    class Meta:
        model = AtividadeComplementar
        fields = [
            'id_atividade_complementar',
            'descricao',
            'carga_horaria_solicitada',
            'tipo_atividade',
            'tipo_atividade_nome'
        ]

class SubmissaoReadSerializer(serializers.ModelSerializer):
    aluno_nome = serializers.ReadOnlyField(source = 'aluno.usuario.nome')
    curso_nome = serializers.ReadOnlyField(source = 'curso.nome')
    coordenador_nome = serializers.ReadOnlyField(source = 'coordenador.usuario.nome')
    status_submissao_nome = serializers.ReadOnlyField(source = 'status_submissao.nome_status')
    carga_horaria_solicitada = serializers.ReadOnlyField(source = 'atividade_complementar.carga_horaria_solicitada')
    atividade_categoria = serializers.ReadOnlyField(source='atividade_complementar.tipo_atividade.nome')
    certificado_url = serializers.ReadOnlyField(source= 'certificado.url_arquivo')
    certificado_nome = serializers.ReadOnlyField(source='certificado.nome_arquivo')
    class Meta:
        model = Submissao
        fields = [
            'id_submissao',
            'data_envio',
            'observacao_coordenador',
            'aluno',
            'aluno_nome',
            'curso',
            'curso_nome',
            'atividade_complementar',
            'atividade_categoria',
            'status_submissao',
            'status_submissao_nome',
            'certificado',
            'coordenador',
            'coordenador_nome',
            'carga_horaria_aprovada',
            'carga_horaria_solicitada',
            'certificado_url',
            'certificado_nome'
        ]

class SubmissaoCreateSerializer(serializers.ModelSerializer):
    certificado_arquivo = serializers.FileField(write_only=True, required=True)
    class Meta:
        model = Submissao
        fields = ['curso', 'atividade_complementar', 'certificado_arquivo']

    def validate(self, attrs):
        curso = attrs.get('curso')
        atividade = attrs.get('atividade_complementar')

        if Submissao.objects.filter(atividade_complementar = atividade).exists():
            raise serializers.ValidationError(
                'Essa atividade complementar já foi submetida.'
            )
        existe_regra = RegraAtividade.objects.filter(
            curso = curso,
            tipo_atividade = atividade.tipo_atividade
        ).exists()

        if not existe_regra:
            raise serializers.ValidationError(
                'Não existe regra de atividade para esse curso e tipo de atividade.'
            )

        if 'aluno' in self.initial_data:
            raise serializers.ValidationError({
                'aluno': 'Este campo não pode ser enviado.'
            })

        return attrs

class SubmissaoUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Submissao
        fields =['observacao_coordenador', 'status_submissao','carga_horaria_aprovada']

class CursoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Curso
        fields = '__all__'

class LogAuditoriaReadSerializer(serializers.ModelSerializer):
    usuario_nome = serializers.ReadOnlyField(source ='usuario.nome')
    tipo_acao_nome = serializers.ReadOnlyField(source = 'tipo_acao.acao')
    usuario_email = serializers.ReadOnlyField(source='usuario.email')
    
    class Meta:
        model = LogAuditoria
        fields = [
            'id_log_auditoria',
            'data_hora',
            'nome_entidade',
            'id_entidade_afetada',
            'descricao',
            'ip_origem',
            'usuario',
            'usuario_nome',
            'usuario_email',
            'tipo_acao',
            'tipo_acao_nome',
            'valor_anterior',
            'valor_novo'
        ]

class NotificacaoEmailReadSerializer(serializers.ModelSerializer):
    submissao_id = serializers.IntegerField(source='submissao.id_submissao', read_only=True)

    class Meta:
        model = NotificacaoEmail
        fields = [
            'id_notificacao_email',
            'assunto',
            'corpo',
            'data',
            'destinatario',
            'status_envio',
            'tipo_evento',
            'mensagem_erro',
            'submissao_id'
        ]

class RecuperarSenhaSerializer(serializers.Serializer):
    email = serializers.EmailField()

class RedefinirSenhaSerializer(serializers.Serializer):
    token = serializers.CharField()
    nova_senha = serializers.CharField(min_length=6)

class CertificadoExtracaoSerializer(serializers.Serializer):
    certificado_arquivo = serializers.FileField(required=True)
    

    def validate_certificado_arquivo(self, value):
        extensoes_permitidas = ["pdf", "png", "jpg", "jpeg"]
        extensao = value.name.split(".")[-1].lower()
        if extensao not in extensoes_permitidas:
            raise serializers.ValidationError("Envie um arquivo PDF ou imagem PNG/JPG/JPEG.")
        return value