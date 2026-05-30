import json
from google import genai
from google.genai import types
from django.conf import settings


class CertificadoExtracaoService:

    @staticmethod
    def extrair_texto_arquivo(arquivo):
        return arquivo

    @staticmethod
    def extrair_dados(arquivo):
        client = genai.Client(
            api_key=settings.GEMINI_API_KEY
        )

        conteudo = arquivo.read()
        mime_type = arquivo.content_type or "application/pdf"

        prompt = """
Analise este certificado acadêmico.

Retorne APENAS um JSON válido neste formato:

{
  "carga_horaria": "",
  "data_certificado": "",
  "curso": "",
  "instituicao": "",
  "texto_extraido": ""
}

Regras:
- Não invente informações.
- Se não encontrar um campo, retorne string vazia.
- Data no formato YYYY-MM-DD.
- Curso pode ser curso, palestra, workshop, minicurso, evento ou atividade complementar.
- Em texto_extraido retorne o texto principal identificado no certificado.
"""

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                types.Part.from_bytes(
                    data=conteudo,
                    mime_type=mime_type
                ),
                prompt
            ],
        )

        texto = response.text.strip()

        if texto.startswith("```json"):
            texto = texto.replace("```json", "").replace("```", "").strip()

        try:
            return json.loads(texto)
        except Exception:
            return {
                "carga_horaria": "",
                "data_certificado": "",
                "curso": "",
                "instituicao": "",
                "texto_extraido": texto
            }