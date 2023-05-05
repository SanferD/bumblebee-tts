import * as path from 'path'
import * as cdk from 'aws-cdk-lib';
import * as s3 from 'aws-cdk-lib/aws-s3'
import * as sqs from 'aws-cdk-lib/aws-sqs'
import * as lambda from 'aws-cdk-lib/aws-lambda'
import * as lambdaEventSources from 'aws-cdk-lib/aws-lambda-event-sources'
import * as python from '@aws-cdk/aws-lambda-python-alpha'
import { Construct } from 'constructs';

const FFMPEG_LAYER_ARN = "arn:aws:lambda:us-east-1:180797159824:layer:ffmpeg:2"

export interface LambdasStackProps extends cdk.StackProps {
    dataBucket: s3.Bucket
    clipsQueue: sqs.Queue
    visibilityTimeout: cdk.Duration
}

export class LambdasStack extends cdk.Stack {

    readonly clipper: lambda.Function
    readonly phraser: lambda.Function

    constructor(scope: Construct, id: string, props: LambdasStackProps) {
        super(scope, id, props);

        const timeoutDuration = cdk.Duration.minutes(   props.visibilityTimeout.toMinutes()/6   )
        const codePath = path.join(__dirname, "..", "..", "app")

        this.clipper = this.createLambdaFunction({ codePath, timeoutDuration, index: "clipper.py", props });
        const ffmpegLayer = lambda.LayerVersion.fromLayerVersionArn(this, "ffmpeg-layer", FFMPEG_LAYER_ARN);
        this.clipper.addLayers(ffmpegLayer);

        this.phraser = this.createLambdaFunction({ codePath, timeoutDuration, index: "phraser.py", props });
        const clipsQueueEventSource = new lambdaEventSources.SqsEventSource(props.clipsQueue)
        this.phraser.addEventSource(clipsQueueEventSource)
  }

    private createLambdaFunction({ codePath, timeoutDuration, index, props }: createLambdaFunctionProps) : lambda.Function {
        const _id = index.split(".")[0]
        const id = _id[0].toUpperCase() + _id.slice(1, _id.length)
        return new python.PythonFunction(this, id, {
            entry: codePath,
            runtime: lambda.Runtime.PYTHON_3_10,
            handler: "handle",
            index,
            timeout: timeoutDuration,
            environment: {
                BUCKET_NAME: props.dataBucket.bucketName,
                CLIPS_QUEUE_URL: props.clipsQueue.queueUrl,
            },
        });
    }

}

interface createLambdaFunctionProps {
    codePath: string
    index: string
    props: LambdasStackProps
    timeoutDuration: cdk.Duration
}

