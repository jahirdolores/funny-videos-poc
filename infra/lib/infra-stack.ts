import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';

import * as path from 'path';

import * as s3 from 'aws-cdk-lib/aws-s3';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as apigwv2 from 'aws-cdk-lib/aws-apigatewayv2';

import { HttpLambdaIntegration } from 'aws-cdk-lib/aws-apigatewayv2-integrations';


export class InfraStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // =========================
    // S3 - Videos
    // =========================
    const uploads = new s3.Bucket(this, 'Uploads', {
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      encryption: s3.BucketEncryption.S3_MANAGED,
      enforceSSL: true,

      lifecycleRules: [
        {
          expiration: cdk.Duration.days(7),
        },
      ],

      cors: [
        {
          allowedMethods: [s3.HttpMethods.PUT],
          allowedOrigins: ['*'],
          allowedHeaders: ['*'],
        },
      ],

      removalPolicy: cdk.RemovalPolicy.DESTROY,
      autoDeleteObjects: true,
    });

    // =========================
    // DynamoDB - Jobs
    // =========================
    const jobs = new dynamodb.TableV2(this, 'Jobs', {
      partitionKey: {
        name: 'jobId',
        type: dynamodb.AttributeType.STRING,
      },

      billing: dynamodb.Billing.onDemand(),

      timeToLiveAttribute: 'ttl',

      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    // =========================
    // Lambda - API
    // =========================
    const apiFn = new lambda.Function(this, 'ApiFn', {
      runtime: lambda.Runtime.PYTHON_3_13,
      handler: 'handler.handler',

      code: lambda.Code.fromAsset(
        path.join(__dirname, '../../lambdas/api')
      ),

      timeout: cdk.Duration.seconds(10),

      environment: {
        TABLE_NAME: jobs.tableName,
        BUCKET_NAME: uploads.bucketName,
      },
    });

    // Permisos de Lambda
    uploads.grantPut(apiFn);
    jobs.grantReadWriteData(apiFn);

    // =========================
    // API Gateway - HTTP API
    // =========================
    const api = new apigwv2.HttpApi(this, 'Api', {
      corsPreflight: {
        allowOrigins: ['*'],

        allowMethods: [
          apigwv2.CorsHttpMethod.GET,
          apigwv2.CorsHttpMethod.POST,
        ],

        allowHeaders: ['content-type'],
      },
    });

    // Conectar API Gateway con Lambda
    const integration = new HttpLambdaIntegration(
      'ApiIntegration',
      apiFn
    );

    // POST /jobs
    api.addRoutes({
      path: '/jobs',
      methods: [apigwv2.HttpMethod.POST],
      integration,
    });

    // GET /jobs/{jobId}
    api.addRoutes({
      path: '/jobs/{jobId}',
      methods: [apigwv2.HttpMethod.GET],
      integration,
    });

    // =========================
    // Outputs
    // =========================
    new cdk.CfnOutput(this, 'UploadsBucketName', {
      value: uploads.bucketName,
    });

    new cdk.CfnOutput(this, 'JobsTableName', {
      value: jobs.tableName,
    });

    new cdk.CfnOutput(this, 'ApiUrl', {
      value: api.apiEndpoint,
    });
  }
}