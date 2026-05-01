-- Aprova uma submissão válida, registrando o coordenador responsável e a observação.
CREATE OR REPLACE PROCEDURE sp_aprovar_submissao(
    p_id_submissao integer,
    p_id_coordenador integer,
    p_obs text,
    p_carga_horaria_aprovada integer
)
LANGUAGE plpgsql
AS
$$
DECLARE
    v_curso integer;
BEGIN
    SELECT s."idCurso"
    INTO v_curso
    FROM "Submissao" s
    WHERE s."idSubmissao" = p_id_submissao;

    IF NOT fn_usuario_coordena_curso(p_id_coordenador, v_curso) THEN
        RAISE EXCEPTION 'Coordenador não pertence ao curso';
    END IF;

    UPDATE "Submissao"
    SET "statusSubmissao" = 2,
        "observacaoCoordenador" = p_obs,
        "idCoordenador" = p_id_coordenador,
        "cargaHorariaAprovada" = p_carga_horaria_aprovada
    WHERE "idSubmissao" = p_id_submissao;

    IF NOT fn_submissao_pode_ser_aprovada(p_id_submissao) THEN
        RAISE EXCEPTION 'Submissao invalida';
    END IF;
END;
$$;


-- Reprova uma submissão, registrando o coordenador responsável e a observação.
CREATE PROCEDURE sp_reprovar_submissao(
    p_id_submissao integer,
    p_id_coordenador integer,
    p_obs text
)
LANGUAGE plpgsql
AS
$$
BEGIN
    UPDATE "Submissao"
    SET "statusSubmissao" = 3,
        "observacaoCoordenador" = p_obs,
        "idCoordenador" = p_id_coordenador
    WHERE "idSubmissao" = p_id_submissao;
END;
$$;


-- Cadastra um usuário e, em seguida, cria seu vínculo como aluno.
CREATE PROCEDURE sp_cadastrar_aluno_com_usuario(
    p_nome varchar,
    p_email varchar,
    p_senha text,
    p_matricula varchar
)
LANGUAGE plpgsql
AS
$$
DECLARE v_id integer;
BEGIN
    INSERT INTO "Usuario"(nome,email,"senhaHash")
    VALUES(p_nome,p_email,p_senha)
    RETURNING "idUsuario" INTO v_id;

    INSERT INTO "Aluno"
    VALUES(v_id,0,p_matricula);
END;
$$;


-- Cadastra um usuário e, em seguida, cria seu vínculo como coordenador.
CREATE PROCEDURE sp_cadastrar_coordenador_com_usuario(
    p_nome varchar,
    p_email varchar,
    p_senha text,
    p_telefone varchar DEFAULT NULL
)
LANGUAGE plpgsql
AS
$$
DECLARE 
    v_id integer;
BEGIN
    -- Cria o usuário
    INSERT INTO "Usuario"(nome, email, "senhaHash")
    VALUES(p_nome, p_email, p_senha)
    RETURNING "idUsuario" INTO v_id;

    -- Cria o coordenador
    INSERT INTO "Coordenador"
    VALUES(v_id, true);

    -- Se telefone foi informado, cadastra
    IF p_telefone IS NOT NULL THEN
        INSERT INTO "Telefone"(numero, "idUsuario")
        VALUES(p_telefone, v_id);
    END IF;
END;
$$;

--  Edição de coordenador, sem mudar os telefones
CREATE PROCEDURE sp_atualizar_coordenador_com_usuario(
    p_id_usuario integer,
    p_nome varchar DEFAULT NULL,
    p_email varchar DEFAULT NULL,
    p_status boolean DEFAULT NULL
)
LANGUAGE plpgsql
AS
$$
DECLARE
    v_existe_coordenador integer;
    v_email_em_uso integer;
BEGIN
    -- Verifica se o coordenador existe
    SELECT COUNT(*)
    INTO v_existe_coordenador
    FROM public."Coordenador"
    WHERE "idUsuario" = p_id_usuario;

    IF v_existe_coordenador = 0 THEN
        RAISE EXCEPTION 'Coordenador não encontrado.';
    END IF;

    -- Verifica se o novo email já está sendo usado por outro usuário
    IF p_email IS NOT NULL AND btrim(p_email) <> '' THEN
        SELECT COUNT(*)
        INTO v_email_em_uso
        FROM public."Usuario"
        WHERE email = p_email
          AND "idUsuario" <> p_id_usuario;

        IF v_email_em_uso > 0 THEN
            RAISE EXCEPTION 'Já existe outro usuário com este email.';
        END IF;
    END IF;

    -- Atualiza os dados de Usuario
    UPDATE public."Usuario"
    SET
        nome = CASE
            WHEN p_nome IS NOT NULL AND btrim(p_nome) <> '' THEN p_nome
            ELSE nome
        END,
        email = CASE
            WHEN p_email IS NOT NULL AND btrim(p_email) <> '' THEN p_email
            ELSE email
        END
    WHERE "idUsuario" = p_id_usuario;

    -- Atualiza os dados de Coordenador
    UPDATE public."Coordenador"
    SET
        status = CASE
            WHEN p_status IS NOT NULL THEN p_status
            ELSE status
        END
    WHERE "idUsuario" = p_id_usuario;
END;
$$;

-- Update aluno e usuario
CREATE PROCEDURE sp_atualizar_aluno_com_usuario(
    p_id_usuario integer,
    p_nome varchar DEFAULT NULL,
    p_email varchar DEFAULT NULL,
    p_matricula varchar DEFAULT NULL
)
LANGUAGE plpgsql
AS
$$
DECLARE
    v_existe_aluno integer;
    v_email_em_uso integer;
    v_matricula_em_uso integer;
BEGIN
    -- Verifica se o aluno existe
    SELECT COUNT(*)
    INTO v_existe_aluno
    FROM public."Aluno"
    WHERE "idUsuario" = p_id_usuario;

    IF v_existe_aluno = 0 THEN
        RAISE EXCEPTION 'Aluno não encontrado.';
    END IF;

    -- Verifica se o novo email já está sendo usado por outro usuário
    IF p_email IS NOT NULL AND btrim(p_email) <> '' THEN
        SELECT COUNT(*)
        INTO v_email_em_uso
        FROM public."Usuario"
        WHERE email = p_email
          AND "idUsuario" <> p_id_usuario;

        IF v_email_em_uso > 0 THEN
            RAISE EXCEPTION 'Já existe outro usuário com este email.';
        END IF;
    END IF;

    -- Verifica se a nova matrícula já está sendo usada por outro aluno
    IF p_matricula IS NOT NULL AND btrim(p_matricula) <> '' THEN
        SELECT COUNT(*)
        INTO v_matricula_em_uso
        FROM public."Aluno"
        WHERE matricula = p_matricula
          AND "idUsuario" <> p_id_usuario;

        IF v_matricula_em_uso > 0 THEN
            RAISE EXCEPTION 'Já existe outro aluno com esta matrícula.';
        END IF;
    END IF;

    -- Atualiza os dados de Usuario
    UPDATE public."Usuario"
    SET
        nome = CASE
            WHEN p_nome IS NOT NULL AND btrim(p_nome) <> '' THEN p_nome
            ELSE nome
        END,
        email = CASE
            WHEN p_email IS NOT NULL AND btrim(p_email) <> '' THEN p_email
            ELSE email
        END
    WHERE "idUsuario" = p_id_usuario;

    -- Atualiza os dados de Aluno
    UPDATE public."Aluno"
    SET
        matricula = CASE
            WHEN p_matricula IS NOT NULL AND btrim(p_matricula) <> '' THEN p_matricula
            ELSE matricula
        END
    WHERE "idUsuario" = p_id_usuario;
END;
$$;



-- Matricula um aluno em um curso, impedindo matrícula duplicada.
CREATE PROCEDURE sp_matricular_aluno_em_curso(
    p_aluno integer,
    p_curso integer,
    p_status integer
)
LANGUAGE plpgsql
AS
$$
BEGIN
    IF EXISTS (
        SELECT 1 FROM "Matricula"
        WHERE "Aluno_idUsuario" = p_aluno
          AND "Curso_idCurso" = p_curso
    ) THEN
        RAISE EXCEPTION 'Aluno já matriculado';
    END IF;

    INSERT INTO "Matricula"
    ("Curso_idCurso", "Aluno_idUsuario", "dataMatricula", "idStatusMatricula")
    VALUES (p_curso, p_aluno, CURRENT_DATE, p_status);
END;
$$;


-- Vincula um coordenador a um curso com data de início da coordenação.
CREATE PROCEDURE sp_vincular_coordenador_curso(
    p_coord integer,
    p_curso integer
)
LANGUAGE plpgsql
AS
$$
BEGIN
    INSERT INTO "CoordenacaoCurso"
    ("Curso_idCurso", "Coordenador_idUsuario", "dataInicio", "dataFim")
    VALUES (p_curso, p_coord, CURRENT_DATE, NULL);
END;
$$;


-- Registra uma nova submissão de atividade complementar enviada por um aluno.
CREATE PROCEDURE sp_registrar_submissao(
    p_aluno integer,
    p_atividade integer,
    p_certificado integer
)
LANGUAGE plpgsql
AS
$$
BEGIN
    INSERT INTO "Submissao"
    ("dataEnvio","idAluno","atividadeComplementa","statusSubmissao",certificado)
    VALUES(
        CURRENT_DATE,
        p_aluno,
        p_atividade,
        1,
        p_certificado
    );
END;
$$;
