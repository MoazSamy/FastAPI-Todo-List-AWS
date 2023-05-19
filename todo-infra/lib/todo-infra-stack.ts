import * as cdk from 'aws-cdk-lib';
import * as ddb from 'aws-cdk-lib/aws-dynamodb';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import { Construct } from 'constructs';

export class TodoInfraStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // Create DDB table to store the tasks.
    const table = new ddb.Table(this, "Tasks", {
      // This is the index column of the table
      partitionKey: { name: "task_id", type: ddb.AttributeType.STRING},
      billingMode: ddb.BillingMode.PAY_PER_REQUEST,
      // This allows the records to be automatically deleted so the database doesn't get clogged with unnecessary data
      // NOT GOOD FOR PRODUCTION ONLY FOR EDUCATIONAL PURPOSES
      timeToLiveAttribute: "ttl",
    });
    
    // Add GSI based on user_id
    // This indexes the user_id column so that the records are searchable using the user_id sorting it by the time of creation DESC or ASC. This makes the query operations much faster since the column is pre-indexed. This makes all the lookups using user_id field run in O(n).
    table.addGlobalSecondaryIndex({
      indexName: "user-index",
      partitionKey: { name : "user_id", type: ddb.AttributeType.STRING},
      sortKey: {name: "created_time", type: ddb.AttributeType.NUMBER},
    });

    // Create a Lambda function for this API
    const api = new lambda.Function(this, "API", {
      runtime: lambda.Runtime.PYTHON_3_10,
      // This gets uploaded to Lambda from the local file.
      code: lambda.Code.fromAsset("../api/lambda_function.zip"),
      // This tells Lambda to excute this function when it's invoked.
      handler: "todo.handler",
      // Global virables for Lambda
      environment:{
        TABLE_NAME: table.tableName,
      }
    });
    
    // Create a URL so we can access the function/
    const functionUrl = api.addFunctionUrl({
      authType: lambda.FunctionUrlAuthType.NONE,
      // Adding Cross-Origin resource sharing as some browsers have difficulties connecting to the APIs without them.
      cors:{
        allowedOrigins: ["*"],
        allowedMethods: [lambda.HttpMethod.ALL],
        allowedHeaders: ["*"],
      },
    });

    // Output the API function url
    new cdk.CfnOutput(this, "APIUrl", {
      value: functionUrl.url,
    });

    // Give Lambda permissions to r/w to the table explicitly.
    table.grantReadWriteData(api);
  }
}
