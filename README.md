# Funny Videos PoC

Prueba de concepto en AWS para analizar videos cortos y generar ideas de contenido humorístico.

El usuario sube un video y escribe qué quiere lograr. El sistema analiza el video y posteriormente generará una propuesta con:

- concepto
- guion por momentos
- memes sugeridos
- música
- tendencias
- texto para publicar

> Esta PoC no edita ni genera el video. Solo genera la idea.

---

## Arquitectura

```text
Web
 |
 | POST /jobs
 v
API Gateway
 |
 v
Lambda API
 | \
 |  \----> DynamoDB
 |
 └-------> URL prefirmada
              |
              v
              S3
              |
              | ObjectCreated
              v
         Lambda Procesar
              |
              v
          Amazon Bedrock
```

Arquitectura final prevista:

```text
Página web
    |
    v
API Gateway
    |
    v
Lambda API
    |
    +----> DynamoDB
    |
    +----> Presigned URL
              |
              v
             S3
              |
              v
       Lambda Procesar
              |
       +------+------+
       |             |
       v             v
   Bedrock       APIs externas
   Nova 2 Lite   Imgflip/Jamendo
```

---

## Servicios AWS

- Amazon S3
- AWS Lambda
- Amazon DynamoDB
- Amazon API Gateway
- Amazon Bedrock
- AWS IAM
- AWS Systems Manager Parameter Store
- Amazon CloudWatch
- AWS CloudFormation
- AWS CDK

---

## Tecnologías

### Infraestructura

- AWS CDK
- TypeScript
- Node.js

### Backend

- Python 3.13
- boto3

### Frontend

- HTML
- CSS
- JavaScript

---

## Región

El proyecto utiliza:

```text
us-east-1
```

---

## Modelo de IA

```text
Amazon Nova 2 Lite
us.amazon.nova-2-lite-v1:0
```

---

## Estructura del proyecto

```text
funny-videos-poc/
├── infra/
│   ├── bin/
│   │   └── infra.ts
│   └── lib/
│       └── infra-stack.ts
│
├── lambdas/
│   ├── api/
│   │   └── handler.py
│   └── procesar/
│
├── scripts/
│   └── probar_video.py
│
├── web/
│
├── docs/
│
├── .gitignore
└── README.md
```

---

## Requisitos

- AWS CLI v2
- AWS CDK v2
- Node.js 22+
- Python 3.12+
- Git
- GitHub CLI

Verificar:

```bash
aws --version
cdk --version
node --version
python3.13 --version
git --version
gh --version
```

---

## Configuración AWS

Configurar credenciales:

```bash
aws configure
```

Verificar identidad:

```bash
aws sts get-caller-identity
```

Configurar la región:

```bash
export AWS_REGION=us-east-1
export AWS_DEFAULT_REGION=us-east-1
```

Obtener el Account ID:

```bash
export ACCOUNT_ID=$(aws sts get-caller-identity \
  --query Account \
  --output text)
```

Verificar:

```bash
echo $ACCOUNT_ID
```

---

## CDK Bootstrap

Preparar la cuenta para desplegar infraestructura con AWS CDK:

```bash
cdk bootstrap aws://$ACCOUNT_ID/us-east-1
```

Verificar:

```bash
aws cloudformation describe-stacks \
  --stack-name CDKToolkit \
  --query 'Stacks[0].StackStatus'
```

Resultado esperado:

```text
CREATE_COMPLETE
```

---

## Flujo de trabajo con CDK

Compilar TypeScript:

```bash
npm run build
```

Generar la plantilla de CloudFormation:

```bash
cdk synth
```

Revisar qué cambiaría en AWS:

```bash
cdk diff
```

Desplegar:

```bash
cdk deploy
```

Eliminar la infraestructura:

```bash
cdk destroy
```

### Diferencia entre los comandos

```text
cdk synth
→ genera la plantilla de CloudFormation

cdk diff
→ muestra qué cambios se harían en AWS

cdk deploy
→ aplica realmente los cambios en AWS

cdk destroy
→ elimina los recursos del stack
```

---

## Recursos desplegados actualmente

### S3 Uploads

Bucket privado utilizado para almacenar los videos.

Configuración:

- acceso público bloqueado
- cifrado administrado por S3
- conexiones solo mediante HTTPS
- CORS habilitado para `PUT`
- archivos eliminados después de 7 días
- `RemovalPolicy.DESTROY`
- `autoDeleteObjects: true`

Los videos no son públicos.

Más adelante el cliente podrá subir archivos mediante una URL prefirmada de S3.

---

### DynamoDB Jobs

Tabla utilizada para almacenar los trabajos asociados a cada video.

Partition key:

```text
jobId
```

Tipo:

```text
String
```

Billing:

```text
PAY_PER_REQUEST
```

TTL:

```text
ttl
```

Ejemplo de registro:

```json
{
  "jobId": "b8cf74af-f665-4cf5-a722-2ad9151cc9bb",
  "status": "PENDING_UPLOAD",
  "prompt": "hazlo gracioso",
  "videoKey": "uploads/b8cf74af-f665-4cf5-a722-2ad9151cc9bb/video.mp4",
  "createdAt": "2026-10-11T04:30:00Z",
  "ttl": 1760761800
}
```

---

## Estados de un trabajo

Flujo normal:

```text
PENDING_UPLOAD
      |
      v
ANALYZING
      |
      v
SEARCHING
      |
      v
WRITING
      |
      v
DONE
```

En caso de error:

```text
FAILED
```

---

## Prueba de Amazon Bedrock

Antes de construir toda la infraestructura se probó Amazon Bedrock con texto y video.

El modelo utilizado es:

```text
us.amazon.nova-2-lite-v1:0
```

El proyecto incluye el script:

```text
scripts/probar_video.py
```

Activar el entorno virtual:

```bash
source .venv/bin/activate
```

Ejecutar:

```bash
python scripts/probar_video.py ~/Downloads/video.mp4
```

El script:

1. lee el video local
2. llama a Amazon Bedrock mediante boto3
3. envía el video a Nova 2 Lite
4. solicita una descripción segundo a segundo
5. imprime la respuesta y el consumo de tokens

Ejemplo del flujo:

```text
Video local
    |
    v
Python
    |
    v
boto3
    |
    v
Amazon Bedrock
    |
    v
Nova 2 Lite
```

---

## Entorno virtual de Python

El proyecto utiliza un entorno virtual para evitar modificar la instalación global de Python.

Crear:

```bash
python3.13 -m venv .venv
```

Activar:

```bash
source .venv/bin/activate
```

Instalar boto3:

```bash
pip install --upgrade boto3
```

Verificar:

```bash
python --version
pip show boto3
```

Salir del entorno virtual:

```bash
deactivate
```

---

## API

La API tendrá inicialmente dos endpoints.

### Crear trabajo

```http
POST /jobs
```

Entrada:

```json
{
  "prompt": "hazlo gracioso",
  "contentType": "video/mp4"
}
```

Respuesta:

```json
{
  "jobId": "uuid",
  "uploadUrl": "https://..."
}
```

Responsabilidades:

- validar el prompt
- validar el tipo de video
- generar un UUID
- guardar el trabajo en DynamoDB
- generar una URL prefirmada
- devolver el `jobId`
- devolver la URL de subida

---

### Consultar trabajo

```http
GET /jobs/{jobId}
```

Devuelve el registro almacenado en DynamoDB.

Ejemplo:

```json
{
  "jobId": "uuid",
  "status": "PENDING_UPLOAD",
  "prompt": "hazlo gracioso",
  "videoKey": "uploads/uuid/video.mp4",
  "createdAt": "2026-10-11T04:30:00Z",
  "ttl": 1760761800
}
```

---

## URLs prefirmadas de S3

El video no pasa por Lambda ni por API Gateway.

Flujo:

```text
Cliente
   |
   | POST /jobs
   v
API Gateway
   |
   v
Lambda API
   |
   +------> DynamoDB
   |
   | genera presigned URL
   v
Cliente
   |
   | PUT video
   v
S3
```

Esto permite subir archivos directamente a S3.

Ventajas:

- evita enviar archivos grandes a Lambda
- evita límites de tamaño de API Gateway
- reduce tráfico innecesario
- mejora la escalabilidad
- mantiene el bucket privado

La URL prefirmada será temporal.

---

## Lambda API

La función Lambda se encuentra en:

```text
lambdas/api/handler.py
```

La Lambda recibe variables de entorno desde CDK:

```text
TABLE_NAME
BUCKET_NAME
```

Estas variables contienen los nombres reales de:

- la tabla DynamoDB
- el bucket S3

De esta forma no se escriben nombres físicos de recursos directamente en el código Python.

---

## Permisos IAM

CDK genera los permisos necesarios para la Lambda.

La Lambda API necesita:

```text
DynamoDB
├── lectura
└── escritura

S3
└── escritura
```

En CDK:

```ts
uploads.grantPut(apiFn);
jobs.grantReadWriteData(apiFn);
```

Esto evita crear políticas IAM manualmente.

---

## API Gateway

Se utilizará:

```text
API Gateway HTTP API
```

En lugar de REST API.

Las primeras rutas serán:

```text
POST /jobs
GET  /jobs/{jobId}
```

Flujo:

```text
Usuario
   |
   v
API Gateway
   |
   v
Lambda API
```

---

## CORS

API Gateway tendrá CORS habilitado para permitir llamadas desde el frontend.

Métodos permitidos:

```text
GET
POST
```

S3 tendrá CORS para:

```text
PUT
```

Esto permitirá que el navegador pueda:

```text
Frontend
   |
   +---- POST ----> API Gateway
   |
   +---- PUT -----> S3
```

---

## Outputs del stack

El stack devuelve actualmente:

```text
UploadsBucketName
JobsTableName
```

La Fase 3 agregará:

```text
ApiUrl
```

Estos valores se muestran después de ejecutar:

```bash
cdk deploy
```

Ejemplo:

```text
Outputs:

InfraStack.JobsTableName = ...
InfraStack.UploadsBucketName = ...
InfraStack.ApiUrl = ...
```

---

## Verificación de S3

Listar buckets:

```bash
aws s3 ls
```

Buscar el bucket de uploads:

```bash
aws s3 ls | grep -i uploads
```

Listar archivos del bucket:

```bash
aws s3 ls s3://NOMBRE_BUCKET/ --recursive
```

---

## Verificación de DynamoDB

Listar tablas:

```bash
aws dynamodb list-tables
```

Formato más limpio:

```bash
aws dynamodb list-tables \
  --query 'TableNames'
```

Consultar un trabajo:

```bash
aws dynamodb get-item \
  --table-name NOMBRE_TABLA \
  --key '{"jobId":{"S":"JOB_ID"}}'
```

---

## Logs

Para consultar funciones Lambda:

```bash
aws lambda list-functions \
  --query 'Functions[].FunctionName'
```

Ver logs en tiempo real:

```bash
aws logs tail /aws/lambda/NOMBRE_FUNCION --follow
```

---

## Errores de CloudFormation

Consultar eventos recientes del stack:

```bash
aws cloudformation describe-stack-events \
  --stack-name InfraStack \
  --max-items 15
```

Esto es útil cuando un `cdk deploy` falla.

---

## Budget

Se configuró un AWS Budget de:

```text
USD 5 por mes
```

con una alerta al alcanzar aproximadamente el 80%.

Es decir:

```text
USD 4 aproximadamente
```

El budget solo notifica.

No bloquea automáticamente el consumo.

---

## Git y GitHub

El proyecto utiliza Git para control de versiones.

Repositorio:

```text
funny-videos-poc
```

El repositorio se mantiene privado durante la fase inicial de desarrollo.

Comandos principales:

```bash
git status
git add .
git commit -m "mensaje"
git push
```

GitHub CLI:

```bash
gh auth status
gh repo view
```

---

## .gitignore

No se deben subir al repositorio:

```text
.venv/
node_modules/
cdk.out/
.env
logs
archivos temporales del sistema
```

Esto evita:

- subir dependencias innecesarias
- subir artefactos generados
- subir secretos
- aumentar innecesariamente el tamaño del repositorio

---

## Convención de commits

Ejemplos de commits utilizados en el proyecto:

```text
chore: initialize AWS funny videos PoC

docs: add project README

feat: add S3 uploads bucket and DynamoDB jobs table

feat: add jobs API with Lambda and API Gateway

feat: process uploaded videos with Bedrock

feat: add meme and music sources

feat: add web interface
```

---

## Arquitectura prevista al finalizar

```text
                    ┌───────────────┐
                    │   Página web  │
                    └───────┬───────┘
                            |
                       POST /jobs
                            |
                            v
                    ┌───────────────┐
                    │ API Gateway   │
                    └───────┬───────┘
                            |
                            v
                    ┌───────────────┐
                    │  Lambda API   │
                    └───┬───────┬───┘
                        |       |
                        |       |
                        v       v
                   DynamoDB   Presigned URL
                                |
                                v
                               S3
                                |
                         ObjectCreated
                                |
                                v
                     ┌───────────────────┐
                     │ Lambda Procesar  │
                     └───────┬───────────┘
                             |
                  ┌──────────┼──────────┐
                  |          |          |
                  v          v          v
              Bedrock     Imgflip    Jamendo
                  |
                  v
           Web Grounding
                  |
                  v
              DynamoDB
                  |
                  v
             Página web
```

---

## Fases del proyecto

### Fase 0 — Preparación

- [x] Instalar AWS CLI
- [x] Instalar AWS CDK
- [x] Configurar Python 3.13
- [x] Configurar Node.js
- [x] Configurar credenciales AWS
- [x] Configurar región
- [x] Ejecutar CDK Bootstrap
- [x] Crear AWS Budget

### Fase 1 — Amazon Bedrock

- [x] Probar Nova 2 Lite con texto
- [x] Crear entorno virtual Python
- [x] Instalar boto3
- [x] Probar Nova 2 Lite con video
- [x] Verificar uso de tokens

### Fase 2 — Infraestructura base

- [x] Crear proyecto CDK
- [x] Crear bucket S3
- [x] Configurar cifrado
- [x] Configurar CORS
- [x] Configurar lifecycle de 7 días
- [x] Crear tabla DynamoDB
- [x] Configurar TTL
- [x] Ejecutar `cdk synth`
- [x] Ejecutar `cdk diff`
- [x] Ejecutar `cdk deploy`
- [x] Verificar recursos

### Fase 3 — API

- [ ] Crear Lambda API
- [ ] Agregar permisos IAM
- [ ] Crear API Gateway
- [ ] Crear `POST /jobs`
- [ ] Crear `GET /jobs/{jobId}`
- [ ] Generar URL prefirmada de S3
- [ ] Probar subida de video
- [ ] Consultar trabajo en DynamoDB

### Fase 4 — Procesamiento automático

- [ ] Crear Lambda `ProcesarFn`
- [ ] Configurar evento `ObjectCreated` de S3
- [ ] Leer video desde S3
- [ ] Invocar Amazon Bedrock
- [ ] Generar ficha del video
- [ ] Actualizar estado en DynamoDB
- [ ] Manejar errores

### Fase 5 — Fuentes externas

- [ ] Integrar Imgflip
- [ ] Integrar Jamendo
- [ ] Guardar credencial Jamendo en Parameter Store
- [ ] Integrar Nova Web Grounding
- [ ] Guardar citas
- [ ] Generar idea final

### Fase 6 — Frontend

- [ ] Crear `web/index.html`
- [ ] Selector de video
- [ ] Campo de prompt
- [ ] Subida directa a S3
- [ ] Polling cada 3 segundos
- [ ] Mostrar progreso
- [ ] Mostrar idea final
- [ ] Mostrar fuentes
- [ ] Validar tipo y tamaño del archivo

### Fase 7 — Publicación

- [ ] Crear bucket para frontend
- [ ] Crear CloudFront
- [ ] Desplegar sitio web
- [ ] Verificar HTTPS

### Fase 8 — Limpieza

- [ ] Ejecutar `cdk destroy`
- [ ] Eliminar parámetros de SSM
- [ ] Eliminar AWS Budget si ya no se necesita
- [ ] Verificar eliminación de recursos

---

## Objetivo de aprendizaje

Este proyecto busca practicar de forma integrada:

- Infrastructure as Code
- AWS CDK
- CloudFormation
- Amazon S3
- DynamoDB
- AWS Lambda
- API Gateway
- IAM
- Amazon Bedrock
- URLs prefirmadas
- arquitecturas event-driven
- integración con APIs externas
- observabilidad con CloudWatch
- control de costos
- Git y GitHub

La implementación se realiza por fases para entender cada servicio antes de agregar el siguiente componente.
