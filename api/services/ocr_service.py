import re
import pdfplumber
import numpy as np
from PIL import Image
from paddleocr import PaddleOCR


class CertificadoExtracaoService:
    reader = None

    @classmethod
    def get_reader(cls):
        if cls.reader is None:
            cls.reader = PaddleOCR(
                use_angle_cls=True,
                lang="pt"
            )
        return cls.reader

    @staticmethod
    def extrair_texto_arquivo(arquivo):
        extensao = arquivo.name.split(".")[-1].lower()

        if extensao == "pdf":
            return CertificadoExtracaoService.extrair_texto_pdf(arquivo)

        if extensao in ["png", "jpg", "jpeg"]:
            return CertificadoExtracaoService.extrair_texto_imagem(arquivo)

        return ""

    @staticmethod
    def extrair_texto_pdf(arquivo):
        texto = ""

        with pdfplumber.open(arquivo) as pdf:
            for pagina in pdf.pages:
                conteudo = pagina.extract_text()

                if conteudo and conteudo.strip():
                    texto += conteudo + "\n"
                else:
                    imagem = pagina.to_image(resolution=200).original
                    texto_ocr = CertificadoExtracaoService.extrair_texto_imagem_pil(imagem)
                    texto += texto_ocr + "\n"

        return texto.strip()

    @staticmethod
    def extrair_texto_imagem(arquivo):
        imagem = Image.open(arquivo).convert("RGB")
        return CertificadoExtracaoService.extrair_texto_imagem_pil(imagem)

    @staticmethod
    def extrair_texto_imagem_pil(imagem):
        reader = CertificadoExtracaoService.get_reader()

        imagem_np = np.array(imagem)

        resultado = reader.ocr(imagem_np, cls=True)

        textos = []

        if resultado and resultado[0]:
            for linha in resultado[0]:
                texto = linha[1][0]
                textos.append(texto)

        return " ".join(textos)

    @staticmethod
    def extrair_dados(texto):
        dados = {
            "texto_extraido": texto or ""
        }

        match_carga = re.search(
            r'(\d+)\s*(horas|hora|h)\b',
            texto,
            re.IGNORECASE
        )

        if match_carga:
            dados["carga_horaria"] = match_carga.group(1)

        match_data = re.search(r'\b\d{2}/\d{2}/\d{4}\b', texto)

        if match_data:
            dia, mes, ano = match_data.group().split("/")
            dados["data_certificado"] = f"{ano}-{mes}-{dia}"

        match_curso = re.search(
            r'(curso de|curso em|participou do curso de|concluiu o curso de)\s*(.+)',
            texto,
            re.IGNORECASE
        )

        if match_curso:
            dados["curso"] = match_curso.group(2).strip()

        match_instituicao = re.search(
            r'(instituição|emitido por|oferecido por)\s*[:\-]?\s*(.+)',
            texto,
            re.IGNORECASE
        )

        if match_instituicao:
            dados["instituicao"] = match_instituicao.group(2).strip()

        return dados