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


def extraer_json(texto):
    inicio = texto.find("{")
    fin = texto.rfind("}")

    if inicio == -1 or fin == -1:
        raise ValueError("Bedrock no devolvió un JSON válido")

    return json.loads(texto[inicio:fin + 1])


def handler(event, context):
    for record in event.get("Records", []):
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
        print(f"Ignorando key inesperada: {key}")
        return

    job_id = partes[1]

    try:
        # Evitar procesar dos veces el mismo evento de S3
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

        prompt_usuario = job.get("prompt", "")

        prompt = PROMPT_FICHA.format(
            prompt_usuario=prompt_usuario
        )

        formato = "mov" if key.lower().endswith(".mov") else "mp4"

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
                                        "uri": f"s3://{bucket}/{key}",
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

        print(
            f"Ficha generada correctamente "
            f"para job {job_id}"
        )

    except Exception as error:
        print(
            f"Error procesando job {job_id}: {error}"
        )

        table.update_item(
            Key={
                "jobId": job_id
            },
            UpdateExpression="SET #s = :estado, #e = :error",
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