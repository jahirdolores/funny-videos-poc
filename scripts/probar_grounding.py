import boto3
from botocore.config import Config


bedrock = boto3.client(
    "bedrock-runtime",
    region_name="us-east-1",
    config=Config(read_timeout=120),
)

response = bedrock.converse(
    modelId="us.amazon.nova-2-lite-v1:0",
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "text": (
                        "Busca en la web tendencias actuales de memes o audios "
                        "que podrían funcionar para un video corto gracioso de un perro. "
                        "Dame 3 ejemplos breves."
                    )
                }
            ],
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

for bloque in response["output"]["message"]["content"]:
    if "text" in bloque:
        print("\nTEXTO:")
        print(bloque["text"])

    if "citationsContent" in bloque:
        print("\nCITAS:")
        for cita in bloque["citationsContent"]["citations"]:
            web = cita.get("location", {}).get("web", {})
            print(
                "-",
                web.get("domain", ""),
                web.get("url", "")
            )