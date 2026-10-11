import sys
import boto3
from botocore.config import Config

bedrock = boto3.client(
    "bedrock-runtime",
    region_name="us-east-1",
    config=Config(read_timeout=300)
)

with open(sys.argv[1], "rb") as f:
    video = f.read()

resp = bedrock.converse(
    modelId="us.amazon.nova-2-lite-v1:0",
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "video": {
                        "format": "mp4",
                        "source": {
                            "bytes": video
                        }
                    }
                },
                {
                    "text": (
                        "Describe qué pasa en este video segundo a segundo "
                        "y di cuál es el momento más gracioso."
                    )
                }
            ]
        }
    ],
    inferenceConfig={
        "maxTokens": 1500
    }
)

for bloque in resp["output"]["message"]["content"]:
    if "text" in bloque:
        print(bloque["text"])

print("\nUso:")
print(resp["usage"])

