-- Retorna o papel do usuário no sistema (ALUNO, COORDENADOR, SUPERADMIN ou USUARIO).
CREATE FUNCTION fn_obter_papel_usuario(p_id_usuario integer)
RETURNS varchar
LANGUAGE plpgsql
AS
$$
DECLARE
    v_papel varchar;
BEGIN
    IF EXISTS (SELECT 1 FROM "Aluno" WHERE "idUsuario" = p_id_usuario) THEN
        v_papel := 'ALUNO';

    ELSIF EXISTS (SELECT 1 FROM "Coordenador" WHERE "idUsuario" = p_id_usuario) THEN
        v_papel := 'COORDENADOR';

    ELSIF EXISTS (SELECT 1 FROM "SuperAdmin" WHERE "idUsuario" = p_id_usuario) THEN
        v_papel := 'SUPERADMIN';

    ELSE
        v_papel := 'USUARIO';
    END IF;

    RETURN v_papel;
END;
$$;


-- Calcula o total de horas aprovadas de atividades complementares de um aluno.
CREATE OR REPLACE FUNCTION fn_total_horas_aprovadas_aluno(p_id_aluno integer)
RETURNS numeric
LANGUAGE plpgsql
AS
$$
DECLARE
    total numeric;
BEGIN
    SELECT COALESCE(SUM(s."cargaHorariaAprovada"), 0)
    INTO total
    FROM "Submissao" s
    WHERE s."idAluno" = p_id_aluno
      AND s."statusSubmissao" = 2;

    RETURN total;
END;
$$;


-- Retorna quantas horas ainda faltam para o aluno cumprir a carga mínima do curso.
CREATE FUNCTION fn_horas_restantes_aluno(
    p_id_aluno integer,
    p_id_curso integer
)
RETURNS numeric
LANGUAGE plpgsql
AS
$$
DECLARE
    v_total numeric;
    v_minimo integer;
BEGIN
    SELECT "cargaHorariaMinima"
    INTO v_minimo
    FROM "Curso"
    WHERE "idCurso" = p_id_curso;

    v_total := fn_total_horas_aprovadas_aluno(p_id_aluno);

    RETURN GREATEST(v_minimo - v_total, 0);
END;
$$;


-- Retorna quantas horas ainda podem ser aproveitadas para um tipo de atividade no curso.
CREATE OR REPLACE FUNCTION fn_limite_disponivel_tipo(
    p_id_aluno integer,
    p_id_curso integer,
    p_id_tipo integer
)
RETURNS numeric
LANGUAGE plpgsql
AS
$$
DECLARE
    v_limite integer;
    v_usado numeric;
BEGIN
    SELECT "limiteHoras"
    INTO v_limite
    FROM "RegraAtividade"
    WHERE "Curso_idCurso" = p_id_curso
      AND "TipoAtividade_idTipoAtividade" = p_id_tipo;

    SELECT COALESCE(SUM(s."cargaHorariaAprovada"), 0)
    INTO v_usado
    FROM "Submissao" s
    JOIN "AtividadeComplementar" ac
      ON ac."idAtividadeComplementar" = s."atividadeComplementa"
    WHERE s."idAluno" = p_id_aluno
      AND s."statusSubmissao" = 2
      AND ac."tipoAtividade" = p_id_tipo;

    RETURN GREATEST(v_limite - v_usado, 0);
END;
$$;


-- Verifica se uma submissão pode ser aprovada com base no limite de horas do tipo de atividade.
CREATE OR REPLACE FUNCTION fn_submissao_pode_ser_aprovada(p_id_submissao integer)
RETURNS boolean
LANGUAGE plpgsql
AS
$$
DECLARE
    v_tipo integer;
    v_curso integer;
    v_aluno integer;
    v_restante numeric;
    v_carga integer;
BEGIN
    SELECT
        ac."tipoAtividade",
        s."idCurso",
        s."idAluno",
        s."cargaHorariaAprovada"
    INTO v_tipo, v_curso, v_aluno, v_carga
    FROM "Submissao" s
    JOIN "AtividadeComplementar" ac
      ON ac."idAtividadeComplementar" = s."atividadeComplementa"
    WHERE s."idSubmissao" = p_id_submissao
    LIMIT 1;

    IF v_carga IS NULL THEN
        RETURN false;
    END IF;

    v_restante := fn_limite_disponivel_tipo(v_aluno, v_curso, v_tipo);

    IF v_carga > v_restante THEN
        RETURN false;
    END IF;

    RETURN true;
END;
$$;


-- Verifica se um usuário é coordenador ativo de um determinado curso.
CREATE FUNCTION fn_usuario_coordena_curso(
    p_id_usuario integer,
    p_id_curso integer
)
RETURNS boolean
LANGUAGE plpgsql
AS
$$
BEGIN
    RETURN EXISTS (
        SELECT 1
        FROM "CoordenacaoCurso"
        WHERE "Coordenador_idUsuario" = p_id_usuario
          AND "Curso_idCurso" = p_id_curso
          AND "dataFim" IS NULL
    );
END;
$$;

CREATE OR REPLACE FUNCTION fn_log_auditoria_submissao()
RETURNS TRIGGER AS $$
DECLARE
    v_usuario_id INTEGER;
    v_ip_origem VARCHAR(45);
    v_id_tipo_acao INTEGER;
    v_descricao TEXT;
    v_nome_entidade VARCHAR(100) := 'Submissao';
    v_status_aprovado INTEGER;
    v_status_rejeitado INTEGER;
BEGIN
    -- contexto vindo da aplicação
    v_usuario_id := NULLIF(current_setting('app.usuario_id', true), '')::INTEGER;
    v_ip_origem := NULLIF(current_setting('app.ip_origem', true), '');

    -- busca os ids dos status relevantes
    SELECT "idStatusSubmissao"
    INTO v_status_aprovado
    FROM "StatusSubmissao"
    WHERE "nomeStatus" = 'APROVADO'
    LIMIT 1;

    SELECT "idStatusSubmissao"
    INTO v_status_rejeitado
    FROM "StatusSubmissao"
    WHERE "nomeStatus" = 'REJEITADO'
    LIMIT 1;

    IF TG_OP = 'INSERT' THEN
        SELECT "idTipoAcao"
        INTO v_id_tipo_acao
        FROM "TipoAcao"
        WHERE "acao" = 'CREATE'
        LIMIT 1;

        v_descricao := 'Submissão criada';

        INSERT INTO "LogAuditoria" (
            "dataHora",
            "nomeEntidade",
            "idEntidadeAfetada",
            "descricao",
            "ipOrigem",
            "idUsuario",
            "idTipoAcao",
            "valorAnterior",
            "valorNovo"
        )
        VALUES (
            CURRENT_TIMESTAMP,
            v_nome_entidade,
            NEW."idSubmissao",
            v_descricao,
            v_ip_origem,
            v_usuario_id,
            v_id_tipo_acao,
            NULL,
            row_to_json(NEW)::jsonb
        );

        RETURN NEW;
    END IF;

    IF TG_OP = 'UPDATE' THEN
        IF OLD."statusSubmissao" IS DISTINCT FROM NEW."statusSubmissao"
           AND NEW."statusSubmissao" = v_status_aprovado THEN

            SELECT "idTipoAcao"
            INTO v_id_tipo_acao
            FROM "TipoAcao"
            WHERE "acao" = 'APPROVE'
            LIMIT 1;

            v_descricao := 'Submissão aprovada';

        ELSIF OLD."statusSubmissao" IS DISTINCT FROM NEW."statusSubmissao"
              AND NEW."statusSubmissao" = v_status_rejeitado THEN

            SELECT "idTipoAcao"
            INTO v_id_tipo_acao
            FROM "TipoAcao"
            WHERE "acao" = 'REFUSE'
            LIMIT 1;

            v_descricao := 'Submissão rejeitada';

        ELSE
            SELECT "idTipoAcao"
            INTO v_id_tipo_acao
            FROM "TipoAcao"
            WHERE "acao" = 'UPDATE'
            LIMIT 1;

            v_descricao := 'Submissão atualizada';
        END IF;

        INSERT INTO "LogAuditoria" (
            "dataHora",
            "nomeEntidade",
            "idEntidadeAfetada",
            "descricao",
            "ipOrigem",
            "idUsuario",
            "idTipoAcao",
            "valorAnterior",
            "valorNovo"
        )
        VALUES (
            CURRENT_TIMESTAMP,
            v_nome_entidade,
            NEW."idSubmissao",
            v_descricao,
            v_ip_origem,
            v_usuario_id,
            v_id_tipo_acao,
            row_to_json(OLD)::jsonb,
            row_to_json(NEW)::jsonb
        );

        RETURN NEW;
    END IF;

    IF TG_OP = 'DELETE' THEN
        SELECT "idTipoAcao"
        INTO v_id_tipo_acao
        FROM "TipoAcao"
        WHERE "acao" = 'DELETE'
        LIMIT 1;

        v_descricao := 'Submissão excluída';

        INSERT INTO "LogAuditoria" (
            "dataHora",
            "nomeEntidade",
            "idEntidadeAfetada",
            "descricao",
            "ipOrigem",
            "idUsuario",
            "idTipoAcao",
            "valorAnterior",
            "valorNovo"
        )
        VALUES (
            CURRENT_TIMESTAMP,
            v_nome_entidade,
            OLD."idSubmissao",
            v_descricao,
            v_ip_origem,
            v_usuario_id,
            v_id_tipo_acao,
            row_to_json(OLD)::jsonb,
            NULL
        );

        RETURN OLD;
    END IF;

    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

SELECT fn_obter_papel_usuario(1);
SELECT fn_total_horas_aprovadas_aluno(3);
SELECT fn_horas_restantes_aluno(3, 2);
SELECT fn_limite_disponivel_tipo(3, 2, 3);
SELECT fn_submissao_pode_ser_aprovada(1);
SELECT fn_usuario_coordena_curso(13, 1);
