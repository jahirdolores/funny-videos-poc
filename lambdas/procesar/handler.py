from fuentes import obtener_memes, obtener_musica

import json
import os
import urllib.parse

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError


TABLE_NAME = os.environ["TABLE_NAME"]
MODEL_ID = os.environ["MODEL_ID"]
ACCOUNT_ID = os.environ["ACCOUNT_ID"]

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)

bedrock = boto3.client(
    "bedrock-runtime",
    region_name="us-east-1",
    config=Config(read_timeout=280)
)


PROMPT_FICHA = """
Eres analista visual de videos cortos para contenido de humor.

Analiza TODO el video cuidadosamente.

Presta especial atención a:
- movimientos pequeños o repetitivos
- temblores
- movimientos de patas, cabeza, boca, ojos o cola
- cambios breves de postura
- detalles visuales que podrían pasar desapercibidos
- el momento visual más gracioso

Devuelve SOLO un JSON con esta forma:

{{
  "resumen": "una frase objetiva sobre lo que ocurre",
  "duracion_aprox_s": 0,
  "sujetos": ["descripción visual del sujeto"],
  "escenario": "descripción objetiva del lugar",
  "linea_de_tiempo": [
    {{
      "t_inicio": 0,
      "t_fin": 0,
      "que_pasa": "descripción precisa de lo visible",
      "potencial_comico": 1
    }}
  ],
  "movimientos_sutiles": [
    {{
      "parte_del_cuerpo": "",
      "t_inicio": 0,
      "t_fin": 0,
      "descripcion": "",
      "relevancia_comica": 1
    }}
  ],
  "momento_clave": {{
    "t": 0,
    "descripcion": ""
  }},
  "tono_natural": "tierno | absurdo | caótico | tenso",
  "busqueda_musica": {{
    "tags_en_ingles": ["funny", "cute"],
    "velocidad": "medium"
  }},
  "situaciones_memeables": []
}}

Reglas:
- Describe SOLO lo que realmente puedes observar.
- No inventes raza, edad, sexo, emociones ni sonidos.
- Si la raza no es inequívoca, escribe simplemente "perro".
- Revisa específicamente cada extremidad.
- Si observas una pata temblando o moviéndose repetidamente, debe aparecer en "movimientos_sutiles".
- potencial_comico y relevancia_comica van de 1 a 5.
- Los tiempos van en segundos.
- Si no observas movimientos sutiles, devuelve una lista vacía.
- El momento_clave debe basarse en algo realmente visible.

Lo que quiere lograr la persona:
{prompt_usuario}
"""

PROMPT_BRIEF = """
Eres guionista de videos cortos de humor para redes sociales.

Escribe en español de México.

Tu trabajo es proponer UNA idea concreta, original y realizable
para editar el video descrito abajo.

Reglas:
- El video original es el protagonista.
- No inventes acciones que no aparecen en la ficha.
- Cada meme debe entrar en un momento real del video.
- No uses más de un meme cada 4 segundos.
- Explica brevemente por qué funciona cada meme.
- La música debe elegirse SOLO de las pistas proporcionadas.
- No inventes URLs.
- No inventes nombres de pistas.
- Si usas una tendencia encontrada en la investigación,
  debe tener relación con el contenido del video.
- El humor no debe burlarse cruelmente de la persona o mascota.
- Devuelve SOLO JSON válido.

Devuelve exactamente esta estructura:

{{
  "concepto": {{
    "titulo": "",
    "angulo": "",
    "tono": "",
    "por_que_funciona": ""
  }},
  "guion": [
    {{
      "beat": 1,
      "t_inicio": 0,
      "t_fin": 0,
      "que_pasa": "",
      "texto_en_pantalla": ""
    }}
  ],
  "memes": [
    {{
      "nombre": "",
      "tipo": "pip|insert|fullscreen|audio|caption",
      "t": 0,
      "por_que": "",
      "url": ""
    }}
  ],
  "musica": [
    {{
      "titulo": "",
      "artista": "",
      "uso": "fondo",
      "por_que": "",
      "url": "",
      "licencia": ""
    }}
  ],
  "audio_en_tendencia": [
    {{
      "nombre": "",
      "nota": ""
    }}
  ],
  "publicacion": {{
    "caption": "",
    "hashtags": []
  }}
}}

LO QUE PIDIÓ LA PERSONA:
{prompt_usuario}

FICHA DEL VIDEO:
{ficha}

MEMES DISPONIBLES:
{memes}

PISTAS DISPONIBLES:
{pistas}

INVESTIGACIÓN ACTUAL:
{investigacion}
"""

def extraer_json(texto):
    inicio = texto.find("{")
    fin = texto.rfind("}")

    if inicio == -1 or fin == -1:
        raise ValueError("Bedrock no devolvió un JSON válido")

    return json.loads(
        texto[inicio:fin + 1]
    )


def investigar_tendencias(ficha):
    resumen = ficha.get(
        "resumen",
        ""
    )

    situaciones = ficha.get(
        "situaciones_memeables",
        []
    )

    prompt = f"""
Busca en la web tendencias actuales de memes o audios
que puedan funcionar para este video corto.

Resumen del video:
{resumen}

Situaciones memeables:
{json.dumps(situaciones, ensure_ascii=False)}

Dame:
1. Hasta 5 memes o formatos de reacción que encajen.
2. Hasta 3 audios o estilos de audio en tendencia.

Sé breve y usa información actual.
"""

    resp = bedrock.converse(
        modelId=MODEL_ID,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "text": prompt
                    }
                ]
            }
        ],
        toolConfig={
            "tools": [
                {
                    "systemTool": {
                        "name": "nova_grounding"
                    }
                }
            ]
        },
    )

    textos = []
    citas = []

    for bloque in resp["output"]["message"]["content"]:

        if "text" in bloque:
            textos.append(
                bloque["text"]
            )

        if "citationsContent" in bloque:

            for cita in bloque["citationsContent"]["citations"]:

                web = (
                    cita
                    .get("location", {})
                    .get("web", {})
                )

                url = web.get("url")

                if url:
                    citas.append(url)
    citas=list(dict.fromkeys(citas))
    return "\n".join(textos), citas

def generar_brief(
    prompt_usuario,
    ficha,
    memes,
    pistas,
    investigacion
):
    prompt = PROMPT_BRIEF.format(
        prompt_usuario=prompt_usuario,
        ficha=json.dumps(
            ficha,
            ensure_ascii=False
        ),
        memes=json.dumps(
            memes,
            ensure_ascii=False
        ),
        pistas=json.dumps(
            pistas,
            ensure_ascii=False
        ),
        investigacion=investigacion
    )

    resp = bedrock.converse(
        modelId=MODEL_ID,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "text": prompt
                    }
                ]
            }
        ],
        inferenceConfig={
            "maxTokens": 3000
        }
    )

    texto = ""

    for bloque in resp["output"]["message"]["content"]:
        if "text" in bloque:
            texto += bloque["text"]

    return extraer_json(texto)

def handler(event, context):

    for record in event.get(
        "Records",
        []
    ):
        procesar_record(record)

    return {
        "statusCode": 200,
        "body": "OK"
    }


def procesar_record(record):

    bucket = record["s3"]["bucket"]["name"]

    key = urllib.parse.unquote_plus(
        record["s3"]["object"]["key"]
    )

    partes = key.split("/")

    if len(partes) < 3 or partes[0] != "uploads":

        print(
            f"Ignorando key inesperada: {key}"
        )

        return

    job_id = partes[1]

    # =========================
    # Evitar procesar dos veces
    # =========================

    try:

        table.update_item(
            Key={
                "jobId": job_id
            },
            UpdateExpression="SET #s = :nuevo",
            ConditionExpression="#s = :esperado",
            ExpressionAttributeNames={
                "#s": "status"
            },
            ExpressionAttributeValues={
                ":nuevo": "ANALYZING",
                ":esperado": "PENDING_UPLOAD"
            }
        )

    except ClientError as error:

        codigo = error.response["Error"]["Code"]

        if codigo == "ConditionalCheckFailedException":

            print(
                f"Job {job_id} ya fue procesado "
                "o no está en PENDING_UPLOAD"
            )

            return

        raise

    # =========================
    # Procesamiento principal
    # =========================

    try:

        job = table.get_item(
            Key={
                "jobId": job_id
            }
        ).get("Item")

        if not job:

            raise ValueError(
                f"No existe el job {job_id}"
            )

        prompt_usuario = job.get(
            "prompt",
            ""
        )

        prompt = PROMPT_FICHA.format(
            prompt_usuario=prompt_usuario
        )

        formato = (
            "mov"
            if key.lower().endswith(".mov")
            else "mp4"
        )

        # =========================
        # 1. Analizar video
        # =========================

        resp = bedrock.converse(
            modelId=MODEL_ID,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "video": {
                                "format": formato,
                                "source": {
                                    "s3Location": {
                                        "uri": (
                                            f"s3://{bucket}/{key}"
                                        ),
                                        "bucketOwner": ACCOUNT_ID
                                    }
                                }
                            }
                        },
                        {
                            "text": prompt
                        }
                    ]
                }
            ],
            inferenceConfig={
                "maxTokens": 1500
            }
        )

        texto = ""

        for bloque in resp["output"]["message"]["content"]:

            if "text" in bloque:
                texto += bloque["text"]

        ficha = extraer_json(texto)

        # =========================
        # 2. Guardar ficha
        # =========================

        table.update_item(
            Key={
                "jobId": job_id
            },
            UpdateExpression="SET ficha = :ficha",
            ExpressionAttributeValues={
                ":ficha": json.dumps(
                    ficha,
                    ensure_ascii=False
                )
            }
        )

        # =========================
        # 3. Cambiar a SEARCHING
        # =========================

        table.update_item(
            Key={
                "jobId": job_id
            },
            UpdateExpression="SET #s = :s",
            ExpressionAttributeNames={
                "#s": "status"
            },
            ExpressionAttributeValues={
                ":s": "SEARCHING"
            }
        )

        # =========================
        # 4. Buscar memes
        # =========================

        memes = obtener_memes()

        # =========================
        # 5. Buscar música
        # =========================

        busqueda_musica = ficha.get(
            "busqueda_musica",
            {}
        )

        tags = busqueda_musica.get(
            "tags_en_ingles",
            ["funny"]
        )

        velocidad = busqueda_musica.get(
            "velocidad",
            "medium"
        )

        pistas = obtener_musica(
            tags,
            velocidad
        )

        # =========================
        # 6. Web Grounding
        # =========================

        investigacion, citas = investigar_tendencias(
            ficha
        )

        # =========================
        # 7. Cambiar a WRITING
        # =========================

        table.update_item(
            Key={
                "jobId": job_id
            },
            UpdateExpression="SET #s = :s",
            ExpressionAttributeNames={
                "#s": "status"
            },
            ExpressionAttributeValues={
                ":s": "WRITING"
            }
        )

        # =========================
        # 8. Generar brief final
        # =========================

        brief = generar_brief(
            prompt_usuario,
            ficha,
            memes,
            pistas,
            investigacion
        )

        # =========================
        # 9. Guardar resultado final
        # =========================

        table.update_item(
            Key={
                "jobId": job_id
            },
            UpdateExpression=(
                "SET #s = :status, "
                "brief = :brief, "
                "fuentes = :fuentes"
            ),
            ExpressionAttributeNames={
                "#s": "status"
            },
            ExpressionAttributeValues={
                ":status": "DONE",
                ":brief": json.dumps(
                    brief,
                    ensure_ascii=False
                ),
                ":fuentes": json.dumps(
                    citas,
                    ensure_ascii=False
                )
            }
        )

        print(
            f"Job {job_id} terminado correctamente"
            )
    # =========================
    # Manejo de errores
    # =========================

    except Exception as error:

        print(
            f"Error procesando job {job_id}: {error}"
        )

        table.update_item(
            Key={
                "jobId": job_id
            },
            UpdateExpression=(
                "SET #s = :estado, "
                "#e = :error"
            ),
            ExpressionAttributeNames={
                "#s": "status",
                "#e": "error"
            },
            ExpressionAttributeValues={
                ":estado": "FAILED",
                ":error": str(error)
            }
        )

        raise