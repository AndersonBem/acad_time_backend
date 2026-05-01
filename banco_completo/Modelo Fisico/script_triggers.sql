-- FUNÇÃO: atualizar horas do aluno
CREATE FUNCTION trg_atualizar_total_horas_aluno()
RETURNS trigger
LANGUAGE plpgsql
AS
$$
BEGIN
    IF TG_OP IN ('INSERT','UPDATE') THEN
        UPDATE "Aluno"
        SET "totalHoras" = fn_total_horas_aprovadas_aluno(NEW."idAluno")
        WHERE "idUsuario" = NEW."idAluno";
    END IF;

    IF TG_OP IN ('DELETE','UPDATE') THEN
        UPDATE "Aluno"
        SET "totalHoras" = fn_total_horas_aprovadas_aluno(OLD."idAluno")
        WHERE "idUsuario" = OLD."idAluno";
    END IF;

    RETURN NULL;
END;
$$;

-- Atualiza automaticamente o total de horas aprovadas do aluno após inserir, editar ou excluir uma submissão.
CREATE TRIGGER tg_atualizar_total_horas_aluno
AFTER INSERT OR UPDATE OR DELETE
ON "Submissao"
FOR EACH ROW
EXECUTE FUNCTION trg_atualizar_total_horas_aluno();

-- Atualiza automaticamente o total de horas aprovadas do aluno após inserir, editar ou excluir uma submissão.
-- Registra automaticamente no log de auditoria qualquer inserção, atualização ou exclusão feita na tabela Submissao.
-- Impede o cadastro de submissão cuja carga horária ultrapasse o limite permitido para aquele tipo de atividade.
-- Impede que alunos sem matrícula ativa façam novas submissões.
-- Impede alterar o status de uma submissão que já foi finalizada (aprovada ou reprovada).
-- Impede cadastrar vínculo duplicado de coordenação ativa entre o mesmo coordenador e o mesmo curso.

-- -------------------------------------------------------------------------------------------------
-- FUNÇÃO: auditoria
CREATE FUNCTION trg_log_auditoria_submissao()
RETURNS trigger
LANGUAGE plpgsql
AS
$$
DECLARE
    v_tipo integer;
BEGIN
    SELECT "idTipoAcao"
    INTO v_tipo
    FROM "TipoAcao"
    WHERE acao =
        CASE
            WHEN TG_OP='INSERT' THEN 'CREATE'
            WHEN TG_OP='UPDATE' THEN 'UPDATE'
            ELSE 'DELETE'
        END
    LIMIT 1;

    INSERT INTO "LogAuditoria"
    ("dataHora","idEntidadeAfetada",descricao,"ipOrigem","idUsuario","idTipoAcao")
    VALUES(
        CURRENT_DATE,
        COALESCE(NEW."idSubmissao", OLD."idSubmissao"),
        TG_OP,
        '127.0.0.1',
        COALESCE(NEW."idAluno", OLD."idAluno"),
        v_tipo
    );

    RETURN COALESCE(NEW, OLD);
END;
$$;

-- Registra automaticamente no log de auditoria qualquer inserção, atualização ou exclusão feita na tabela Submissao.
CREATE TRIGGER tg_log_auditoria_submissao
AFTER INSERT OR UPDATE OR DELETE
ON "Submissao"
FOR EACH ROW
EXECUTE FUNCTION trg_log_auditoria_submissao();



-- -------------------------------------------------------------------------------------------------



CREATE OR REPLACE FUNCTION trg_validar_limite_horas_submissao()
RETURNS trigger
LANGUAGE plpgsql
AS
$$
DECLARE
    v_tipo integer;
    v_carga integer;
BEGIN
    SELECT
        ac."tipoAtividade",
        ac."cargaHorariaSolicitada"
    INTO
        v_tipo,
        v_carga
    FROM "AtividadeComplementar" ac
    WHERE ac."idAtividadeComplementar" = NEW."atividadeComplementa";

    IF v_tipo IS NULL THEN
        RAISE EXCEPTION 'Atividade complementar % não encontrada', NEW."atividadeComplementa";
    END IF;

    RETURN NEW;
END;
$$;

-- Impede o cadastro de submissão cuja carga horária ultrapasse o limite permitido para aquele tipo de atividade
CREATE TRIGGER tg_validar_limite_horas_submissao
BEFORE INSERT ON "Submissao"
FOR EACH ROW
EXECUTE FUNCTION trg_validar_limite_horas_submissao();

-- -------------------------------------------------------------------------------------------------

CREATE FUNCTION trg_validar_matricula_ativa_submissao()
RETURNS trigger
LANGUAGE plpgsql
AS
$$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM "Matricula" m
        WHERE m."Aluno_idUsuario" = NEW."idAluno"
          AND m."idStatusMatricula" = 1
    ) THEN
        RAISE EXCEPTION 'Aluno % não possui matrícula ativa', NEW."idAluno";
    END IF;

    RETURN NEW;
END;
$$;

-- Impede que alunos sem matrícula ativa façam novas submissões.
CREATE TRIGGER tg_validar_matricula_ativa_submissao
BEFORE INSERT ON "Submissao"
FOR EACH ROW
EXECUTE FUNCTION trg_validar_matricula_ativa_submissao();

-- -------------------------------------------------------------------------------------------------



CREATE FUNCTION trg_bloquear_alteracao_submissao_finalizada()
RETURNS trigger
LANGUAGE plpgsql
AS
$$
BEGIN
    IF OLD."statusSubmissao" IN (2, 3) THEN
        IF NEW."statusSubmissao" <> OLD."statusSubmissao" THEN
            RAISE EXCEPTION 'Submissão já finalizada e não pode ter o status alterado';
        END IF;
    END IF;

    RETURN NEW;
END;
$$;


-- Impede alterar o status de uma submissão que já foi finalizada (aprovada ou reprovada).
CREATE TRIGGER tg_bloquear_alteracao_submissao_finalizada
BEFORE UPDATE ON "Submissao"
FOR EACH ROW
EXECUTE FUNCTION trg_bloquear_alteracao_submissao_finalizada();

-- --------------------------------------------------------------------------------------------------------------------------


CREATE FUNCTION trg_validar_coordenacao_ativa()
RETURNS trigger
LANGUAGE plpgsql
AS
$$
BEGIN
    IF NEW."dataFim" IS NULL THEN
        IF EXISTS (
            SELECT 1
            FROM "CoordenacaoCurso" c
            WHERE c."Curso_idCurso" = NEW."Curso_idCurso"
              AND c."Coordenador_idUsuario" = NEW."Coordenador_idUsuario"
              AND c."dataFim" IS NULL
        ) THEN
            RAISE EXCEPTION 'Já existe vínculo ativo deste coordenador com este curso';
        END IF;
    END IF;

    RETURN NEW;
END;
$$;

-- Impede cadastrar vínculo duplicado de coordenação ativa entre o mesmo coordenador e o mesmo curso.
CREATE TRIGGER tg_validar_coordenacao_ativa
BEFORE INSERT ON "CoordenacaoCurso"
FOR EACH ROW
EXECUTE FUNCTION trg_validar_coordenacao_ativa();



CREATE OR REPLACE FUNCTION public.trg_validar_limite_horas_submissao()
RETURNS trigger
LANGUAGE plpgsql
AS $function$
DECLARE
    v_tipo integer;
    v_curso integer;
    v_carga integer;
    v_limite_restante numeric;
BEGIN
    -- Busca tipo e carga da atividade
    SELECT ac."tipoAtividade", ac."cargaHorariaSolicitada"
    INTO v_tipo, v_carga
    FROM "AtividadeComplementar" ac
    WHERE ac."idAtividadeComplementar" = NEW."atividadeComplementa";

    IF v_tipo IS NULL THEN
        RAISE EXCEPTION 'Atividade complementar % não encontrada', NEW."atividadeComplementa";
    END IF;

    -- Usa o curso informado na própria submissão
    v_curso := NEW."idCurso";

    IF v_curso IS NULL THEN
        RAISE EXCEPTION 'Submissão sem curso informado.';
    END IF;

    -- Verifica o limite restante para o tipo de atividade
    v_limite_restante := fn_limite_disponivel_tipo(
        NEW."idAluno",
        v_curso,
        v_tipo
    );

    IF v_carga > v_limite_restante THEN
        RAISE EXCEPTION
            'Horas excedem o limite permitido para este tipo. Restante: %, solicitado: %',
            v_limite_restante, v_carga;
    END IF;

    RETURN NEW;
END;
$function$;

CREATE OR REPLACE FUNCTION public.trg_validar_matricula_ativa_submissao()
RETURNS trigger
LANGUAGE plpgsql
AS $function$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM "Inscricao" i
        WHERE i."Aluno_idUsuario" = NEW."idAluno"
          AND i."Curso_idCurso" = NEW."idCurso"
          AND i."idStatusMatricula" = 1
    ) THEN
        RAISE EXCEPTION
            'Aluno % não possui inscrição ativa no curso %.',
            NEW."idAluno",
            NEW."idCurso";
    END IF;

    RETURN NEW;
END;
$function$;

CREATE OR REPLACE FUNCTION public.trg_log_auditoria_submissao()
RETURNS trigger
LANGUAGE plpgsql
AS $function$
DECLARE
    v_tipo integer;
BEGIN
    SELECT "idTipoAcao"
    INTO v_tipo
    FROM "TipoAcao"
    WHERE acao =
        CASE
            WHEN TG_OP = 'INSERT' THEN 'CREATE'
            WHEN TG_OP = 'UPDATE' THEN 'UPDATE'
            ELSE 'DELETE'
        END
    LIMIT 1;

    INSERT INTO "LogAuditoria"
    ("dataHora", "idEntidadeAfetada", descricao, "ipOrigem", "idUsuario", "idTipoAcao")
    VALUES (
        CURRENT_TIMESTAMP,
        COALESCE(NEW."idSubmissao", OLD."idSubmissao"),
        TG_OP,
        '127.0.0.1',
        COALESCE(NEW."idAluno", OLD."idAluno"),
        v_tipo
    );

    RETURN COALESCE(NEW, OLD);
END;
$function$;


CREATE OR REPLACE FUNCTION public.trg_validar_aprovacao_submissao()
RETURNS trigger
LANGUAGE plpgsql
AS $function$
DECLARE
    v_tipo integer;
    v_limite_restante numeric;
BEGIN
    -- só valida quando estiver aprovando
    IF NEW."statusSubmissao" = 2 THEN

        IF NEW."cargaHorariaAprovada" IS NULL THEN
            RAISE EXCEPTION 'Carga horária aprovada deve ser informada para aprovar a submissão.';
        END IF;

        SELECT ac."tipoAtividade"
        INTO v_tipo
        FROM "AtividadeComplementar" ac
        WHERE ac."idAtividadeComplementar" = NEW."atividadeComplementa";

        IF v_tipo IS NULL THEN
            RAISE EXCEPTION 'Atividade complementar % não encontrada.', NEW."atividadeComplementa";
        END IF;

        v_limite_restante := fn_limite_disponivel_tipo(
            NEW."idAluno",
            NEW."idCurso",
            v_tipo
        );

        IF NEW."cargaHorariaAprovada" > v_limite_restante THEN
            RAISE EXCEPTION
                'Carga horária aprovada excede o limite permitido para este tipo. Restante: %, aprovada: %',
                v_limite_restante,
                NEW."cargaHorariaAprovada";
        END IF;
    END IF;

    RETURN NEW;
END;
$function$;


DROP TRIGGER IF EXISTS trg_log_auditoria_submissao ON "Submissao";

CREATE TRIGGER trg_log_auditoria_submissao
AFTER INSERT OR UPDATE OR DELETE
ON "Submissao"
FOR EACH ROW
EXECUTE FUNCTION fn_log_auditoria_submissao();

DROP TRIGGER IF EXISTS tg_validar_aprovacao_submissao ON "Submissao";

CREATE TRIGGER tg_validar_aprovacao_submissao
BEFORE UPDATE ON "Submissao"
FOR EACH ROW
EXECUTE FUNCTION trg_validar_aprovacao_submissao();


DROP TRIGGER IF EXISTS tg_log_auditoria_submissao ON "Submissao";
DROP TRIGGER IF EXISTS trg_log_auditoria_submissao ON "Submissao";

DROP FUNCTION IF EXISTS trg_log_auditoria_submissao();
DROP FUNCTION IF EXISTS fn_log_auditoria_submissao();

CREATE TRIGGER trg_log_auditoria_submissao
AFTER INSERT OR UPDATE OR DELETE
ON "Submissao"
FOR EACH ROW
EXECUTE FUNCTION fn_log_auditoria_submissao();