# Funny Videos AI PoC

Aplicación serverless construida en AWS que analiza videos cortos con inteligencia artificial y genera una propuesta creativa para convertirlos en contenido humorístico.

El usuario sube un video, describe qué quiere lograr y el sistema genera:

- concepto creativo
- guion por timestamps
- momentos con potencial cómico
- memes sugeridos
- música
- tendencias
- caption y hashtags
- fuentes utilizadas

> El proyecto no edita ni genera el video final. Genera un brief creativo basado en el contenido real del video.

---

## Demo del flujo

```text
Video + Prompt
      │
      ▼
POST /jobs
      │
      ▼
Presigned S3 URL
      │
      ▼
Upload directo a S3
      │
      ▼
Lambda Procesar
      │
      ├── Amazon Nova 2 Lite
      ├── Imgflip
      ├── Jamendo
      └── Nova Web Grounding
      │
      ▼
DynamoDB
      │
      ▼
Polling desde Next.js
      │
      ▼
Resultado creativo