import * as fs from 'fs'
import * as path from 'path'
import * as cdk from 'aws-cdk-lib';
import * as s3 from 'aws-cdk-lib/aws-s3'
import * as lambda from 'aws-cdk-lib/aws-lambda'
import * as python from '@aws-cdk/aws-lambda-python-alpha'
import { Construct } from 'constructs';

const FFMPEG_LAYER_ARN = "arn:aws:lambda:us-east-1:180797159824:layer:ffmpeg:2"

export interface LambdasStackProps extends cdk.StackProps {
    dataBucket: s3.Bucket
}

export class LambdasStack extends cdk.Stack {
  
    constructor(scope: Construct, id: string, props: LambdasStackProps) {
        super(scope, id, props);

        const codePath = path.join(__dirname, "..", "..", "app")

        const clipper = new python.PythonFunction(this, "Clipper", {
            entry: codePath,
            runtime: lambda.Runtime.PYTHON_3_10,
            handler: "handle",
            index: "clipper.py",
            environment: {
                BUCKET_NAME: props.dataBucket.bucketName,
            },
        })

        const ffmpegLayer = lambda.LayerVersion.fromLayerVersionArn(this, "ffmpeg-layer", FFMPEG_LAYER_ARN)
        clipper.addLayers(ffmpegLayer)
  }
}
