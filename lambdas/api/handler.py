import json
import os
import uuid
import time
from datetime import datetime, timezone

import boto3
from botocore.config import Config


TABLE_NAME = os.environ["TABLE_NAME"]
BUCKET_NAME = os.environ["BUCKET_NAME"]

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)

s3 = boto3.client(
    "s3",
    config=Config(signature_version="s3v4")
)


def response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {
            "content-type": "application/json"
        },
        "body": json.dumps(body)
    }


def handler(event, context):
    route_key = event.get("routeKey")

    if route_key == "POST /jobs":
        return crear_job(event)

    if route_key == "GET /jobs/{jobId}":
        return obtener_job(event)

    return response(404, {"error": "Ruta no encontrada"})


def crear_job(event):
    try:
        body = json.loads(event.get("body") or "{}")
    except json.JSONDecodeError:
        return response(400, {"error": "JSON inválido"})

    promt = body.get("prompt", "").strip()
    content_type = body.get("contentType")

    if not prompt:
        return response(400, {"error": "prompt es obligatorio"})

    if len(prompt) > 500:
        return response(400, {"error": "prompt no puede superar 500 caracteres"})

    if content_type not in ["video/mp4", "video/quicktime"]:
        return response(
            400,
            {"error": "Solo se permite video/mp4 o video/quicktime"}
        )

    job_id = str(uuid.uuid4())

    extension = "mp4" if content_type == "video/mp4" else "mov"
    video_key = f"uploads/{job_id}/video.{extension}"

    created_at = datetime.now(timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )

    ttl = int(time.time()) + 7 * 24 * 60 * 60

    item = {
        "jobId": job_id,
        "status": "PENDING_UPLOAD",
        "prompt": prompt,
        "videoKey": video_key,
        "createdAt": created_at,
        "ttl": ttl
    }

    table.put_item(Item=item)

    upload_url = s3.generate_presigned_url(
        "put_object",
        Params={
            "Bucket": BUCKET_NAME,
            "Key": video_key,
            "ContentType": content_type
        },
        ExpiresIn=900
    )

    return response(
        201,
        {
            "jobId": job_id,
            "uploadUrl": upload_url
        }
    )


def obtener_job(event):
    job_id = event["pathParameters"]["jobId"]

    result = table.get_item(
        Key={"jobId": job_id}
    )

    item = result.get("Item")

    if not item:
        return response(404, {"error": "Trabajo no encontrado"})

    return response(200, item)
