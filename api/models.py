from django.db import models


class Usuario(models.Model):
    id_usuario = models.AutoField(db_column='idUsuario', primary_key=True)
    nome = models.CharField(max_length=150)
    email = models.EmailField(unique=True, max_length=150)
    senha_hash = models.TextField(db_column='senhaHash')

    class Meta:
        managed = False
        db_table = 'Usuario'

    def __str__(self):
        return self.nome
    
    @property
    def is_authenticated(self):
        return True


class Coordenador(models.Model):
    usuario = models.OneToOneField(
        Usuario,
        models.DO_NOTHING,
        db_column='idUsuario',
        primary_key=True,
        related_name='coordenador'
    )
    status = models.BooleanField()

    class Meta:
        managed = False
        db_table = 'Coordenador'

    def __str__(self):
        return self.usuario.nome


class Aluno(models.Model):
    usuario = models.OneToOneField(
        Usuario,
        models.DO_NOTHING,
        db_column='idUsuario',
        primary_key=True,
        related_name='aluno'
    )
    total_horas = models.DecimalField(db_column='totalHoras', max_digits=5, decimal_places=2)
    matricula = models.CharField(unique=True, max_length=30)

    class Meta:
        managed = False
        db_table = 'Aluno'

    def __str__(self):
        return f'{self.usuario.nome} - {self.matricula}'


class SuperAdmin(models.Model):
    usuario = models.OneToOneField(
        Usuario,
        models.DO_NOTHING,
        db_column='idUsuario',
        primary_key=True,
        related_name='superadmin'
    )

    class Meta:
        managed = False
        db_table = 'SuperAdmin'

    def __str__(self):
        return self.usuario.nome


class Curso(models.Model):
    id_curso = models.AutoField(db_column='idCurso', primary_key=True)
    nome = models.CharField(max_length=150)
    carga_horaria_minima = models.IntegerField(db_column='cargaHorariaMinima')
    status = models.BooleanField()
    descricao = models.TextField(blank=True, null=True)
    codigo = models.CharField(unique=True, max_length=30, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'Curso'

    def __str__(self):
        return self.nome


class StatusMatricula(models.Model):
    id_status_matricula = models.AutoField(db_column='idStatusMatricula', primary_key=True)
    nome = models.CharField(max_length=30)

    class Meta:
        managed = False
        db_table = 'StatusMatricula'

    def __str__(self):
        return self.nome


class Inscricao(models.Model):
    id_inscricao = models.AutoField(db_column='idInscricao', primary_key=True)
    curso = models.ForeignKey(Curso, models.DO_NOTHING, db_column='Curso_idCurso')
    aluno = models.ForeignKey(
        Aluno,
        models.DO_NOTHING,
        db_column='Aluno_idUsuario',
        related_name='inscricoes'  
    )
    data_inscricao = models.DateField(db_column='dataInscricao')
    status_matricula = models.ForeignKey(
        StatusMatricula,
        models.DO_NOTHING,
        db_column='idStatusMatricula'
    )

    class Meta:
        managed = False
        db_table = 'Inscricao'
        unique_together = (('curso', 'aluno'),)

    def __str__(self):
        return f'{self.aluno} - {self.curso}'


class CoordenacaoCurso(models.Model):
    id_coordenacao_curso = models.AutoField(db_column='idCoordenacaoCurso', primary_key=True)
    curso = models.ForeignKey(Curso, models.DO_NOTHING, db_column='Curso_idCurso')
    coordenador = models.ForeignKey(Coordenador, models.DO_NOTHING, db_column='Coordenador_idUsuario', related_name='coordenacoes')
    data_inicio = models.DateField(db_column='dataInicio')
    data_fim = models.DateField(db_column='dataFim', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'CoordenacaoCurso'

    def __str__(self):
        return f'{self.coordenador} - {self.curso}'


class Turno(models.Model):
    id_turno = models.AutoField(db_column='idTurno', primary_key=True)
    turno = models.CharField(max_length=30)

    class Meta:
        managed = False
        db_table = 'Turno'

    def __str__(self):
        return self.turno


class TurnoCurso(models.Model):
    turno = models.ForeignKey(Turno, models.DO_NOTHING, db_column='Turno_idTurno')
    curso = models.ForeignKey(Curso, models.DO_NOTHING, db_column='Curso_idCurso')

    class Meta:
        managed = False
        db_table = 'Turno_Curso'
        unique_together = (('turno', 'curso'),)

    def __str__(self):
        return f'{self.turno} - {self.curso}'


class TipoAtividade(models.Model):
    id_tipo_atividade = models.AutoField(db_column='idTipoAtividade', primary_key=True)
    nome = models.CharField(max_length=30, unique=True)

    class Meta:
        managed = False
        db_table = 'TipoAtividade'

    def __str__(self):
        return self.nome


class AtividadeComplementar(models.Model):
    id_atividade_complementar = models.AutoField(db_column='idAtividadeComplementar', primary_key=True)
    descricao = models.TextField(blank=True, null=True)
    carga_horaria_solicitada = models.IntegerField(db_column='cargaHorariaSolicitada')
    tipo_atividade = models.ForeignKey(
        TipoAtividade,
        models.DO_NOTHING,
        db_column='tipoAtividade'
    )

    class Meta:
        managed = False
        db_table = 'AtividadeComplementar'

    def __str__(self):
        return f'Atividade {self.id_atividade_complementar}'


class RegraAtividade(models.Model):
    tipo_atividade = models.ForeignKey(
        TipoAtividade,
        models.DO_NOTHING,
        db_column='TipoAtividade_idTipoAtividade'
    )
    curso = models.ForeignKey(Curso, models.DO_NOTHING, db_column='Curso_idCurso')
    limite_horas = models.IntegerField(db_column='limiteHoras')
    exige_comprovante = models.BooleanField(db_column='exigeComprovante')

    class Meta:
        managed = False
        db_table = 'RegraAtividade'
        unique_together = (('tipo_atividade', 'curso'),)

    def __str__(self):
        return f'{self.tipo_atividade} - {self.curso}'


class Certificado(models.Model):
    id_certificado = models.AutoField(db_column='idCertificado', primary_key=True)
    nome_arquivo = models.CharField(db_column='nomeArquivo', unique=True, max_length=150)
    url_arquivo = models.CharField(db_column='urlArquivo', unique=True, max_length=250, blank=True, null=True)
    texto_extraido_ocr = models.CharField(db_column='textoExtraidoOcr', max_length=250, blank=True, null=True)
    carga_horaria_ocr = models.CharField(db_column='cargaHorariaOcr', max_length=250, blank=True, null=True)
    data_certificado_ocr = models.CharField(db_column='dataCertificadoOcr', max_length=250, blank=True, null=True)
    curso_ocr = models.CharField(db_column='cursoOcr', max_length=250, blank=True, null=True)
    instituicao_ocr = models.CharField(db_column='instituicaoOcr', max_length=250, blank=True, null=True)
    data_upload = models.DateField(db_column='dataUpload')

    class Meta:
        managed = False
        db_table = 'Certificado'

    def __str__(self):
        return self.nome_arquivo


class StatusSubmissao(models.Model):
    id_status_submissao = models.AutoField(db_column='idStatusSubmissao', primary_key=True)
    nome_status = models.CharField(db_column='nomeStatus', max_length=30)

    class Meta:
        managed = False
        db_table = 'StatusSubmissao'

    def __str__(self):
        return self.nome_status


class Submissao(models.Model):
    id_submissao = models.AutoField(db_column='idSubmissao', primary_key=True)
    data_envio = models.DateField(db_column='dataEnvio')
    observacao_coordenador = models.TextField(db_column='observacaoCoordenador', blank=True, null=True)
    aluno = models.ForeignKey(Aluno, models.DO_NOTHING, db_column='idAluno')
    curso = models.ForeignKey(
        Curso,
        models.DO_NOTHING,
        db_column='idCurso'
    )
    
    atividade_complementar = models.OneToOneField(
        AtividadeComplementar,
        models.DO_NOTHING,
        db_column='atividadeComplementa'
    )
    status_submissao = models.ForeignKey(
        StatusSubmissao,
        models.DO_NOTHING,
        db_column='statusSubmissao'
    )
    certificado = models.OneToOneField(Certificado, models.DO_NOTHING, db_column='certificado',
        blank=True,
        null=True  # ⚠️ Temporário
        )
    coordenador = models.ForeignKey(
        Coordenador,
        models.DO_NOTHING,
        db_column='idCoordenador',
        blank=True,
        null=True
    )

    carga_horaria_aprovada = models.IntegerField(
        db_column='cargaHorariaAprovada',
        blank=True,
        null=True
    )

    class Meta:
        managed = False
        db_table = 'Submissao'

    def __str__(self):
        return f'Submissão {self.id_submissao}'


class NotificacaoEmail(models.Model):
    id_notificacao_email = models.AutoField(db_column='idNotificacaoEmail', primary_key=True)
    assunto = models.CharField(max_length=250)
    corpo = models.TextField()
    data = models.DateField()
    destinatario = models.EmailField(max_length=150, null=True, blank=True)
    status_envio = models.CharField(db_column='statusEnvio', max_length=20, null=True, blank=True)
    tipo_evento = models.CharField(db_column='tipoEvento', max_length=50, null=True, blank=True)
    mensagem_erro = models.TextField(db_column='mensagemErro', null=True, blank=True)
    submissao = models.ForeignKey(Submissao, models.DO_NOTHING, db_column='idSubmissao')

    class Meta:
        managed = False
        db_table = 'NotificacaoEmail'

    def __str__(self):
        return self.assunto


class Telefone(models.Model):
    id_telefone = models.AutoField(db_column='idTelefone', primary_key=True)
    numero = models.CharField(unique=True, max_length=20)
    coordenador = models.ForeignKey(Coordenador, models.DO_NOTHING, db_column='idUsuario')

    class Meta:
        managed = False
        db_table = 'Telefone'

    def __str__(self):
        return self.numero


class TipoAcao(models.Model):
    id_tipo_acao = models.AutoField(db_column='idTipoAcao', primary_key=True)
    acao = models.CharField(max_length=20)

    class Meta:
        managed = False
        db_table = 'TipoAcao'

    def __str__(self):
        return self.acao


class LogAuditoria(models.Model):
    id_log_auditoria = models.AutoField(db_column='idLogAuditoria', primary_key=True)
    data_hora = models.DateTimeField(db_column='dataHora')
    nome_entidade = models.CharField(db_column='nomeEntidade', max_length=100)
    id_entidade_afetada = models.IntegerField(db_column='idEntidadeAfetada')
    descricao = models.TextField(blank=True, null=True)
    ip_origem = models.CharField(db_column='ipOrigem', max_length=45, blank=True, null=True)
    usuario = models.ForeignKey(
        Usuario,
        models.DO_NOTHING,
        db_column='idUsuario',
        blank=True,
        null=True
    )
    tipo_acao = models.ForeignKey(
        TipoAcao,
        models.DO_NOTHING,
        db_column='idTipoAcao'
    )
    valor_anterior = models.JSONField(db_column='valorAnterior', blank=True, null=True)
    valor_novo = models.JSONField(db_column='valorNovo', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'LogAuditoria'

    def __str__(self):
        return f'Log {self.id_log_auditoria}'


class RecuperacaoSenha(models.Model):
    id_recuperacao_senha = models.AutoField(db_column='idRecuperacaoSenha', primary_key=True)
    usuario = models.ForeignKey('Usuario', models.DO_NOTHING, db_column='idUsuario')
    token = models.TextField()
    expira_em = models.DateTimeField(db_column='expiraEm')
    usado = models.BooleanField(default=False)
    data_criacao = models.DateTimeField(db_column='dataCriacao')

    class Meta:
        managed = False
        db_table = 'RecuperacaoSenha'