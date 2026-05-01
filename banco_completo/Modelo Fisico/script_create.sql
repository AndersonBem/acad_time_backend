BEGIN;

CREATE TABLE IF NOT EXISTS public."Usuario"
(
    "idUsuario" integer NOT NULL GENERATED ALWAYS AS IDENTITY,
    nome character varying(150) NOT NULL,
    email character varying(150) NOT NULL,
    "senhaHash" text NOT NULL,
    PRIMARY KEY ("idUsuario"),
    UNIQUE (email)
);

CREATE TABLE IF NOT EXISTS public."Coordenador"
(
    "idUsuario" integer NOT NULL,
    status boolean NOT NULL,
    PRIMARY KEY ("idUsuario")
);

CREATE TABLE IF NOT EXISTS public."Aluno"
(
    "idUsuario" integer NOT NULL,
    "totalHoras" numeric(5, 2) NOT NULL,
    matricula character varying(30) NOT NULL,
    PRIMARY KEY ("idUsuario"),
    UNIQUE (matricula)
);

CREATE TABLE IF NOT EXISTS public."Curso"
(
    "idCurso" integer NOT NULL GENERATED ALWAYS AS IDENTITY,
    nome character varying(150) NOT NULL,
    "cargaHorariaMinima" integer NOT NULL,
    status boolean NOT NULL,
    descricao text,
    codigo character varying(30),
    PRIMARY KEY ("idCurso"),
    UNIQUE (codigo)
);

CREATE TABLE IF NOT EXISTS public."Matricula"
(
    "idMatricula" integer NOT NULL GENERATED ALWAYS AS IDENTITY,
    "Curso_idCurso" integer NOT NULL,
    "Aluno_idUsuario" integer NOT NULL,
    "dataMatricula" date NOT NULL,
    "idStatusMatricula" integer NOT NULL,
    PRIMARY KEY ("idMatricula"),
    CONSTRAINT uq_matricula_curso_aluno UNIQUE ("Curso_idCurso", "Aluno_idUsuario")
);

CREATE TABLE IF NOT EXISTS public."CoordenacaoCurso"
(
    "idCoordenacaoCurso" integer NOT NULL GENERATED ALWAYS AS IDENTITY,
    "Curso_idCurso" integer NOT NULL,
    "Coordenador_idUsuario" integer NOT NULL,
    "dataInicio" date NOT NULL,
    "dataFim" date,
    PRIMARY KEY ("idCoordenacaoCurso"),
    CONSTRAINT uq_coordenador_curso UNIQUE ("Curso_idCurso", "Coordenador_idUsuario")
);

CREATE TABLE IF NOT EXISTS public."StatusMatricula"
(
    "idStatusMatricula" integer NOT NULL GENERATED ALWAYS AS IDENTITY,
    nome character varying(30) NOT NULL,
    PRIMARY KEY ("idStatusMatricula")
);

CREATE TABLE IF NOT EXISTS public."SuperAdmin"
(
    "idUsuario" integer NOT NULL,
    PRIMARY KEY ("idUsuario")
);

CREATE TABLE IF NOT EXISTS public."Turno"
(
    "idTurno" integer NOT NULL GENERATED ALWAYS AS IDENTITY,
    turno character varying(30) NOT NULL,
    PRIMARY KEY ("idTurno")
);

CREATE TABLE IF NOT EXISTS public."Turno_Curso"
(
    "Turno_idTurno" integer NOT NULL,
    "Curso_idCurso" integer NOT NULL,
    PRIMARY KEY ("Turno_idTurno", "Curso_idCurso")
);

CREATE TABLE IF NOT EXISTS public."TipoAtividade"
(
    "idTipoAtividade" integer NOT NULL GENERATED ALWAYS AS IDENTITY,
    nome character varying(30) NOT NULL,
    PRIMARY KEY ("idTipoAtividade")
);

CREATE TABLE IF NOT EXISTS public."AtividadeComplementar"
(
    "idAtividadeComplementar" integer NOT NULL GENERATED ALWAYS AS IDENTITY,
    descricao text,
    "cargaHorariaSolicitada" integer NOT NULL,
    "tipoAtividade" integer NOT NULL,
    PRIMARY KEY ("idAtividadeComplementar")
);

CREATE TABLE IF NOT EXISTS public."RegraAtividade"
(
    "TipoAtividade_idTipoAtividade" integer NOT NULL,
    "Curso_idCurso" integer NOT NULL,
    "limiteHoras" integer NOT NULL,
    "exigeComprovante" boolean NOT NULL,
    PRIMARY KEY ("TipoAtividade_idTipoAtividade", "Curso_idCurso")
);

CREATE TABLE IF NOT EXISTS public."Telefone"
(
    "idTelefone" integer NOT NULL GENERATED ALWAYS AS IDENTITY,
    numero character varying(20) NOT NULL,
    "idUsuario" integer NOT NULL,
    PRIMARY KEY ("idTelefone"),
    UNIQUE (numero)
);

CREATE TABLE IF NOT EXISTS public."Submissao"
(
    "idSubmissao" integer NOT NULL GENERATED ALWAYS AS IDENTITY,
    "dataEnvio" date NOT NULL,
    "observacaoCoordenador" text,
    "idAluno" integer NOT NULL,
    "atividadeComplementa" integer NOT NULL,
    "statusSubmissao" integer NOT NULL,
    certificado integer NOT NULL,
    "idCoordenador" integer,
    PRIMARY KEY ("idSubmissao"),
    CONSTRAINT uq_atividade UNIQUE ("atividadeComplementa"),
    CONSTRAINT uq_certificado UNIQUE (certificado)
);

CREATE TABLE IF NOT EXISTS public."StatusSubmissao"
(
    "idStatusSubmissao" integer NOT NULL GENERATED ALWAYS AS IDENTITY,
    "nomeStatus" character varying(30) NOT NULL,
    PRIMARY KEY ("idStatusSubmissao")
);

CREATE TABLE IF NOT EXISTS public."NotificacaoEmail"
(
    "idNotificacaoEmail" integer NOT NULL GENERATED ALWAYS AS IDENTITY,
    assunto character varying(250) NOT NULL,
    corpo text NOT NULL,
    data date NOT NULL,
    "idSubmissao" integer NOT NULL,
    PRIMARY KEY ("idNotificacaoEmail")
);

CREATE TABLE IF NOT EXISTS public."Certificado"
(
    "idCertificado" integer NOT NULL GENERATED ALWAYS AS IDENTITY,
    "nomeArquivo" character varying(150) NOT NULL,
    "urlArquivo" character varying(250),
    PRIMARY KEY ("idCertificado")
);

-- ========================
-- FOREIGN KEYS (PADRONIZADAS)
-- ========================

ALTER TABLE "Coordenador"
ADD CONSTRAINT fk_coordenador_usuario
FOREIGN KEY ("idUsuario") REFERENCES "Usuario"("idUsuario")
ON DELETE CASCADE;

ALTER TABLE "Aluno"
ADD CONSTRAINT fk_aluno_usuario
FOREIGN KEY ("idUsuario") REFERENCES "Usuario"("idUsuario")
ON DELETE CASCADE;

ALTER TABLE "Matricula"
ADD CONSTRAINT fk_matricula_curso
FOREIGN KEY ("Curso_idCurso") REFERENCES "Curso"("idCurso")
ON DELETE CASCADE;

ALTER TABLE "Matricula"
ADD CONSTRAINT fk_matricula_aluno
FOREIGN KEY ("Aluno_idUsuario") REFERENCES "Aluno"("idUsuario")
ON DELETE CASCADE;

ALTER TABLE "Matricula"
ADD CONSTRAINT fk_matricula_status
FOREIGN KEY ("idStatusMatricula") REFERENCES "StatusMatricula"("idStatusMatricula");

ALTER TABLE "CoordenacaoCurso"
ADD CONSTRAINT fk_coordcurso_curso
FOREIGN KEY ("Curso_idCurso") REFERENCES "Curso"("idCurso")
ON DELETE CASCADE;

ALTER TABLE "CoordenacaoCurso"
ADD CONSTRAINT fk_coordcurso_coordenador
FOREIGN KEY ("Coordenador_idUsuario") REFERENCES "Coordenador"("idUsuario")
ON DELETE CASCADE;

-- ========================
-- STATUS PADRÃO
-- ========================

INSERT INTO public."StatusSubmissao" ("nomeStatus")
VALUES 
('PENDENTE'),
('APROVADA'),
('REPROVADA')
ON CONFLICT DO NOTHING;

ALTER TABLE public."Submissao"
ALTER COLUMN "statusSubmissao" SET DEFAULT 1;


ALTER TABLE "Matricula" RENAME TO "Inscricao";

ALTER TABLE "Inscricao"
RENAME COLUMN "idMatricula" TO "idInscricao";

ALTER TABLE "Inscricao"
RENAME CONSTRAINT uq_matricula_curso_aluno TO uq_inscricao_curso_aluno;

ALTER TABLE public."Inscricao"
RENAME COLUMN "dataMatricula" TO "dataInscricao";

ALTER TABLE public."CoordenacaoCurso"
DROP CONSTRAINT uq_coordenador_curso;

CREATE UNIQUE INDEX uq_coordenador_curso_ativo
ON public."CoordenacaoCurso" ("Curso_idCurso", "Coordenador_idUsuario")
WHERE "dataFim" IS NULL;

ALTER TABLE "TipoAtividade"
ADD CONSTRAINT uq_tipo_atividade_nome UNIQUE (nome);

ALTER TABLE "RegraAtividade"
DROP CONSTRAINT "RegraAtividade_pkey";

ALTER TABLE "RegraAtividade"
ADD COLUMN id SERIAL;

ALTER TABLE "RegraAtividade"
ADD PRIMARY KEY (id)

ALTER TABLE "RegraAtividade"
ADD CONSTRAINT uq_regra UNIQUE ("TipoAtividade_idTipoAtividade", "Curso_idCurso");

ALTER TABLE "Submissao"
ADD COLUMN "idCurso" integer;


ALTER TABLE "Submissao"
ADD CONSTRAINT fk_submissao_curso
FOREIGN KEY ("idCurso") REFERENCES "Curso"("idCurso");

ALTER TABLE "Submissao"
ALTER COLUMN "idCurso" SET NOT NULL;


ALTER TABLE "Certificado"
ADD COLUMN "textoExtraidoOcr" varchar(250),
ADD COLUMN "cargaHorariaOcr" varchar(250),
ADD COLUMN "dataCertificadoOcr" varchar(250),
ADD COLUMN "cursoOcr" varchar(250),
ADD COLUMN "instituicaoOcr" varchar(250),
ADD COLUMN "dataUpload" date;


CREATE TABLE IF NOT EXISTS public."TipoAcao"
(
    "idTipoAcao" integer NOT NULL GENERATED ALWAYS AS IDENTITY,
    acao character varying(20) NOT NULL,
    PRIMARY KEY ("idTipoAcao"),
    UNIQUE (acao)
);

CREATE TABLE IF NOT EXISTS public."LogAuditoria"
(
    "idLogAuditoria" integer NOT NULL GENERATED ALWAYS AS IDENTITY,
    "dataHora" timestamp NOT NULL,
    "idEntidadeAfetada" integer NOT NULL,
    descricao text NOT NULL,
    "ipOrigem" character varying(50),
    "idUsuario" integer,
    "idTipoAcao" integer NOT NULL,
    PRIMARY KEY ("idLogAuditoria")
);

ALTER TABLE public."LogAuditoria"
ADD CONSTRAINT fk_logauditoria_usuario
FOREIGN KEY ("idUsuario") REFERENCES "Usuario"("idUsuario")
ON DELETE SET NULL;

ALTER TABLE public."LogAuditoria"
ADD CONSTRAINT fk_logauditoria_tipoacao
FOREIGN KEY ("idTipoAcao") REFERENCES "TipoAcao"("idTipoAcao");

ALTER TABLE "Submissao"
ADD COLUMN "cargaHorariaAprovada" integer;

ALTER TABLE "LogAuditoria"
    ALTER COLUMN "dataHora" TYPE timestamp
    USING "dataHora"::timestamp;

ALTER TABLE "LogAuditoria"
    ADD COLUMN "nomeEntidade" varchar(100);

ALTER TABLE "LogAuditoria"
    ALTER COLUMN "idUsuario" DROP NOT NULL;

ALTER TABLE "LogAuditoria"
    ALTER COLUMN "ipOrigem" DROP NOT NULL;

ALTER TABLE "LogAuditoria"
    ALTER COLUMN "descricao" TYPE text;

ALTER TABLE "LogAuditoria"
    ADD COLUMN "valorAnterior" jsonb;

ALTER TABLE "LogAuditoria"
    ADD COLUMN "valorNovo" jsonb;

ALTER TABLE "NotificacaoEmail"
ADD COLUMN "destinatario" varchar(150),
ADD COLUMN "statusEnvio" varchar(20),
ADD COLUMN "tipoEvento" varchar(50),
ADD COLUMN "mensagemErro" text;


CREATE TABLE "RecuperacaoSenha" (
    "idRecuperacaoSenha" SERIAL PRIMARY KEY,
    "idUsuario" INTEGER NOT NULL,
    "token" TEXT NOT NULL,
    "expiraEm" TIMESTAMP NOT NULL,
    "usado" BOOLEAN NOT NULL DEFAULT FALSE,
    "dataCriacao" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT "fk_recuperacao_usuario"
        FOREIGN KEY ("idUsuario")
        REFERENCES "Usuario" ("idUsuario")
);

END;