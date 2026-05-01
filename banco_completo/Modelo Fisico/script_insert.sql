-- =====================
-- USUARIOS
-- =====================
INSERT INTO "Usuario" (nome, email, "senhaHash") VALUES
('João Silva','joao1@email.com','hash'),
('Maria Souza','maria1@email.com','hash'),
('Pedro Lima','pedro@email.com','hash'),
('Ana Costa','ana@email.com','hash'),
('Carlos Melo','carlos@email.com','hash'),
('Juliana Alves','juliana@email.com','hash'),
('Rafael Gomes','rafael@email.com','hash'),
('Fernanda Rocha','fernanda@email.com','hash'),
('Lucas Martins','lucas@email.com','hash'),
('Bruna Santos','bruna@email.com','hash'),
('Eduardo Nunes','edu@email.com','hash'),
('Patricia Lima','patricia@email.com','hash'),
('Gabriel Dias','gabriel@email.com','hash'),
('Amanda Teixeira','amanda@email.com','hash'),
('Felipe Araújo','felipe@email.com','hash'),
('Larissa Barros','larissa@email.com','hash'),
('Daniel Freitas','daniel@email.com','hash'),
('Camila Torres','camila@email.com','hash'),
('Ricardo Pires','ricardo@email.com','hash'),
('Vanessa Ribeiro','vanessa@email.com','hash');

-- =====================
-- ALUNOS (IDs 1-12)
-- =====================
INSERT INTO "Aluno" VALUES
(1,0,'2023001'),
(2,10,'2023002'),
(3,5,'2023003'),
(4,8,'2023004'),
(5,0,'2023005'),
(6,2,'2023006'),
(7,1,'2023007'),
(8,3,'2023008'),
(9,4,'2023009'),
(10,0,'2023010'),
(11,6,'2023011'),
(12,7,'2023012');

-- =====================
-- COORDENADORES (IDs 13-16)
-- =====================
INSERT INTO "Coordenador" VALUES
(13,true),
(14,true),
(15,true),
(16,true);

-- =====================
-- SUPER ADMIN (ID 17)
-- =====================
INSERT INTO "SuperAdmin" VALUES (17);

-- =====================
-- CURSOS
-- =====================
INSERT INTO "Curso" (nome,"cargaHorariaMinima",status,descricao,codigo) VALUES
('ADS',200,true,'Análise e Desenvolvimento','ADS'),
('SI',180,true,'Sistemas de Informação','SI'),
('Engenharia',300,true,'Engenharia Software','ENG'),
('Direito',100,true,'Curso Direito','DIR'),
('Medicina',400,true,'Curso Medicina','MED');

-- =====================
-- STATUS MATRICULA
-- =====================
INSERT INTO "StatusMatricula" (nome) VALUES
('ATIVO'),('TRANCADO'),('CANCELADO');

-- =====================
-- MATRICULA
-- =====================
INSERT INTO "Matricula"
("Curso_idCurso", "Aluno_idUsuario", "dataMatricula", "idStatusMatricula")
VALUES
(1,1,'2023-01-01',1),
(1,2,'2023-01-01',1),
(2,3,'2023-01-01',1),
(2,4,'2023-01-01',1),
(3,5,'2023-01-01',1),
(3,6,'2023-01-01',1),
(4,7,'2023-01-01',1),
(4,8,'2023-01-01',1),
(5,9,'2023-01-01',1),
(5,10,'2023-01-01',1);

-- =====================
-- COORDENAÇÃO CURSO
-- =====================
INSERT INTO "CoordenacaoCurso"
("Curso_idCurso", "Coordenador_idUsuario", "dataInicio", "dataFim")
VALUES
(1,13,'2023-01-01',NULL),
(2,14,'2023-01-01',NULL),
(3,15,'2023-01-01',NULL),
(4,16,'2023-01-01',NULL);

-- =====================
-- TIPO ATIVIDADE
-- =====================
INSERT INTO "TipoAtividade" (nome) VALUES
('Curso'),
('Palestra'),
('Workshop'),
('Evento'),
('Monitoria');

-- =====================
-- ATIVIDADE COMPLEMENTAR
-- =====================
INSERT INTO "AtividadeComplementar"
(descricao,"cargaHorariaSolicitada","tipoAtividade") VALUES
('Curso Python',20,1),
('Palestra IA',10,2),
('Workshop React',15,3),
('Evento Tech',12,4),
('Monitoria Banco',8,5),
('Curso Java',25,1),
('Palestra Cloud',10,2),
('Workshop Docker',15,3);

-- =====================
-- REGRA ATIVIDADE
-- =====================
INSERT INTO "RegraAtividade" VALUES
(1,1,40,true),
(2,1,30,false),
(3,1,20,true),
(1,2,50,true),
(2,2,30,false);

-- =====================
-- TELEFONE
-- =====================
INSERT INTO "Telefone" (numero,"idUsuario") VALUES
('81999999999',13),
('81988888888',14),
('81977777777',15),
('81966666666',16);

-- =====================
-- CERTIFICADOS
-- =====================
INSERT INTO "Certificado"
("nomeArquivo","urlArquivo","dataUpload") VALUES
('cert1.pdf','url1','2024-01-01'),
('cert2.pdf','url2','2024-01-01'),
('cert3.pdf','url3','2024-01-01'),
('cert4.pdf','url4','2024-01-01'),
('cert5.pdf','url5','2024-01-01');

-- =====================
-- SUBMISSAO
-- =====================
INSERT INTO "Submissao"
("dataEnvio","idAluno","atividadeComplementa","statusSubmissao",certificado,"idCoordenador") VALUES
('2024-01-01',1,1,1,1,13),
('2024-01-02',2,2,1,2,13),
('2024-01-03',3,3,2,3,14),
('2024-01-04',4,4,3,4,14),
('2024-01-05',5,5,1,5,15);

-- =====================
-- NOTIFICAÇÃO
-- =====================
INSERT INTO "NotificacaoEmail"
(assunto,corpo,data,"idSubmissao") VALUES
('Status','Atualizado','2024-01-01',1),
('Status','Atualizado','2024-01-01',2),
('Status','Atualizado','2024-01-01',3);

-- =====================
-- LOG AUDITORIA
-- =====================
INSERT INTO "TipoAcao" (acao) VALUES
('CREATE'),('UPDATE'),('DELETE');

INSERT INTO "LogAuditoria"
("dataHora","idEntidadeAfetada",descricao,"ipOrigem","idUsuario","idTipoAcao") VALUES
('2024-01-01',1,'Criou','127.0.0.1',1,1),
('2024-01-01',2,'Editou','127.0.0.1',2,2),
('2024-01-01',3,'Removeu','127.0.0.1',3,3);

INSERT INTO public."TipoAcao" (acao)
VALUES
('CREATE'),
('UPDATE'),
('DELETE')
ON CONFLICT (acao) DO NOTHING;