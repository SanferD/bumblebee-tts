import * as cdk from 'aws-cdk-lib';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as lambda from 'aws-cdk-lib/aws-lambda'
import * as lambdaEventSources from 'aws-cdk-lib/aws-lambda-event-sources'
import * as path from 'path'
import * as python from '@aws-cdk/aws-lambda-python-alpha'
import * as s3 from 'aws-cdk-lib/aws-s3'
import * as sqs from 'aws-cdk-lib/aws-sqs'
import { Construct } from 'constructs';

const FFMPEG_LAYER_ARN = process.env.FFMPEG_LAYER_ARN
const RAW = "raw"
const PHRASES = "phrases"
const CLIPS = "clips"

export interface LambdasStackProps extends cdk.StackProps {
    dataBucket: s3.Bucket
    rawQueue: sqs.Queue
    clipsQueue: sqs.Queue
    visibilityTimeout: cdk.Duration
}

export class LambdasStack extends cdk.Stack {

    readonly rawAdder: lambda.Function
    readonly clipper: lambda.Function
    readonly phraser: lambda.Function

    constructor(scope: Construct, id: string, props: LambdasStackProps) {
        super(scope, id, props);

        if (FFMPEG_LAYER_ARN === undefined) {
            throw new Error("FFMPEG_LAYER_ARN environment variable is not specified")
        }

        const timeoutDuration = cdk.Duration.minutes(   props.visibilityTimeout.toMinutes()/6   )
        const codePath = path.join(__dirname, "..", "..", "app")

        this.rawAdder = this.createLambdaFunction({ codePath, timeoutDuration, index: "raw_adder.py", props })
        this.addPermissionsToRawAdder(props.dataBucket, props.rawQueue)

        this.clipper = this.createLambdaFunction({ codePath, timeoutDuration, index: "clipper.py", props });
        const ffmpegLayer = lambda.LayerVersion.fromLayerVersionArn(this, "ffmpeg-layer", FFMPEG_LAYER_ARN);
        this.clipper.addLayers(ffmpegLayer);
        const rawQueueEventSource = new lambdaEventSources.SqsEventSource(props.rawQueue)
        this.clipper.addEventSource(rawQueueEventSource)
        this.addPermissionsToClipper(props.dataBucket, props.rawQueue, props.clipsQueue)

        this.phraser = this.createLambdaFunction({ codePath, timeoutDuration, index: "phraser.py", props });
        const clipsQueueEventSource = new lambdaEventSources.SqsEventSource(props.clipsQueue)
        this.phraser.addEventSource(clipsQueueEventSource)
        this.addPermissionsToPhraser(props.dataBucket, props.clipsQueue)
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
                RAW_QUEUE_URL: props.rawQueue.queueUrl,
                // hidden dependencies are difficult to debug, so pass these via environment variables
                RAW_OBJECT_PREFIX: RAW,
                CLIPS_OBJECT_PREFIX: CLIPS,
                PHRASES_OBJECT_PREFIX: PHRASES,
            },
            reservedConcurrentExecutions: 15,
        });
    }

    private addPermissionsToRawAdder(dataBucket: s3.Bucket, rawQueue: sqs.Queue): void {
        this.rawAdder.addToRolePolicy(new iam.PolicyStatement({
            actions: ["s3:ListBucket",],
            resources: [ dataBucket.bucketArn, ]
        }))

        this.rawAdder.addToRolePolicy(new iam.PolicyStatement({
            actions: ["sqs:SendMessage",],
            resources: [ rawQueue.queueArn, ]
        }))
    }

    private addPermissionsToClipper(dataBucket: s3.Bucket, rawQueue: sqs.Queue, clipsQueue: sqs.Queue): void {
        this.clipper.addToRolePolicy(new iam.PolicyStatement({
            actions: ["s3:GetObject", "s3:DeleteObject",],
            resources: [ `${dataBucket.bucketArn}/${RAW}/*`, ]
        }))

        this.clipper.addToRolePolicy(new iam.PolicyStatement({
            actions: ["s3:PutObject",],
            resources: [ `${dataBucket.bucketArn}/${CLIPS}/*`, ]
        }))

        this.clipper.addToRolePolicy(new iam.PolicyStatement({
            actions: ["sqs:SendMessage"],
            resources: [ clipsQueue.queueArn, ]
        }))

        this.clipper.addToRolePolicy(new iam.PolicyStatement({
            actions: ["sqs:RemoveMessage"],
            resources: [ rawQueue.queueArn, ]
        }))
    }

    private addPermissionsToPhraser(dataBucket: s3.Bucket, clipsQueue: sqs.Queue): void {
        this.phraser.addToRolePolicy(new iam.PolicyStatement({
            actions: ["s3:GetObject", "s3:DeleteObject",],
            resources: [`${dataBucket.bucketArn}/${CLIPS}/*`],
        }))

        this.phraser.addToRolePolicy(new iam.PolicyStatement({
            actions: ["s3:PutObject", ],
            resources: [`${dataBucket.bucketArn}/${PHRASES}/*`]
        }))

        this.phraser.addToRolePolicy(new iam.PolicyStatement({
            actions: ["transcribe:StartTranscriptionJob",
                      "transcribe:GetTranscriptionJob",
                      "transcribe:DeleteTranscriptionJob",],
            resources: ["*"], // wildcard is fine since list-transcription-jobs is DENY
        }))

        this.phraser.addToRolePolicy(new iam.PolicyStatement({
            actions: ["sqs:DeleteMessage"],
            resources: [ clipsQueue.queueArn, ]
        }))
    }

}

interface createLambdaFunctionProps {
    codePath: string
    index: string
    props: LambdasStackProps
    timeoutDuration: cdk.Duration
}

