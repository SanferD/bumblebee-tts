import * as cdk from 'aws-cdk-lib';
import * as sqs from 'aws-cdk-lib/aws-sqs'
import { Construct } from 'constructs';

export class SQSStack extends cdk.Stack {

    readonly clipsQueue: sqs.Queue;
    readonly visibilityTimeout: cdk.Duration;

    constructor(scope: Construct, id: string, props?: cdk.StackProps) {
        super(scope, id, props);

        // "set the source queue's visibility timeout to at least six times the timeout that you configure on your function"
        // https://tinyurl.com/2p8dw7yn
        this.visibilityTimeout = cdk.Duration.minutes(15*6)

        this.clipsQueue = new sqs.Queue(this, "ClipsQueue", {
            visibilityTimeout: this.visibilityTimeout,
        })
  }
}
