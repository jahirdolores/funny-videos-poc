import json
import os
import uuid
import time
from decimal import Decimal
from datetime import datetime, timezone

import boto3
from botocore.config import Config


# Variables de entorno configuradas desde CDK
TABLE_NAME = os.environ["TABLE_NAME"]
BUCKET_NAME = os.environ["BUCKET_NAME"]


# Cliente de DynamoDB
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)


# Cliente de S3 con firma v4
s3 = boto3.client(
    "s3",
    config=Config(signature_version="s3v4")
)


def json_default(value):
    """
    DynamoDB devuelve números como Decimal.
    Esta función permite convertirlos a int o float
    antes de generar JSON.
    """
    if isinstance(value, Decimal):
        if value % 1 == 0:
            return int(value)

        return float(value)

    raise TypeError(f"Tipo no serializable: {type(value)}")


def response(status_code, body):
    """
    Construye una respuesta compatible con API Gateway.
    """
    return {
        "statusCode": status_code,
        "headers": {
            "content-type": "application/json"
        },
        "body": json.dumps(
            body,
            default=json_default
        )
    }


def handler(event, context):
    """
    Handler principal de Lambda.

    API Gateway envía routeKey para indicar
    qué endpoint fue utilizado.
    """
    route_key = event.get("routeKey")

    if route_key == "POST /jobs":
        return crear_job(event)

    if route_key == "GET /jobs/{jobId}":
        return obtener_job(event)

    return response(
        404,
        {"error": "Ruta no encontrada"}
    )


def crear_job(event):
    """
    Crea un nuevo trabajo.

    1. Lee el JSON recibido.
    2. Valida prompt y tipo de video.
    3. Genera un jobId.
    4. Guarda el trabajo en DynamoDB.
    5. Genera una URL prefirmada de S3.
    """

    try:
        body = json.loads(event.get("body") or "{}")

    except json.JSONDecodeError:
        return response(
            400,
            {"error": "JSON inválido"}
        )

    # Datos recibidos desde el cliente
    prompt = body.get("prompt", "").strip()
    content_type = body.get("contentType")

    # Validar prompt
    if not prompt:
        return response(
            400,
            {"error": "prompt es obligatorio"}
        )

    if len(prompt) > 500:
        return response(
            400,
            {"error": "prompt no puede superar 500 caracteres"}
        )

    # Validar formato del video
    if content_type not in [
        "video/mp4",
        "video/quicktime"
    ]:
        return response(
            400,
            {
                "error":
                "Solo se permite video/mp4 o video/quicktime"
            }
        )

    # Identificador único para el trabajo
    job_id = str(uuid.uuid4())

    # Elegir extensión dependiendo del Content-Type
    extension = (
        "mp4"
        if content_type == "video/mp4"
        else "mov"
    )

    # Ruta donde se guardará el video en S3
    video_key = (
        f"uploads/{job_id}/video.{extension}"
    )

    # Fecha actual UTC
    created_at = datetime.now(
        timezone.utc
    ).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )

    # El registro expirará dentro de 7 días
    ttl = int(time.time()) + (7 * 24 * 60 * 60)

    # Registro que guardaremos en DynamoDB
    item = {
        "jobId": job_id,
        "status": "PENDING_UPLOAD",
        "prompt": prompt,
        "videoKey": video_key,
        "createdAt": created_at,
        "ttl": ttl
    }

    # Guardar en DynamoDB
    table.put_item(
        Item=item
    )

    # Generar URL temporal para subir directamente a S3
    upload_url = s3.generate_presigned_url(
        "put_object",
        Params={
            "Bucket": BUCKET_NAME,
            "Key": video_key,
            "ContentType": content_type
        },
        ExpiresIn=900
    )

    # 900 segundos = 15 minutos

    return response(
        201,
        {
            "jobId": job_id,
            "uploadUrl": upload_url
        }
    )


def obtener_job(event):
    """
    Consulta un trabajo existente en DynamoDB.
    """

    job_id = event["pathParameters"]["jobId"]

    result = table.get_item(
        Key={
            "jobId": job_id
        }
    )

    item = result.get("Item")

    if not item:
        return response(
            404,
            {"error": "Trabajo no encontrado"}
        )

    return response(
        200,
        item
    )