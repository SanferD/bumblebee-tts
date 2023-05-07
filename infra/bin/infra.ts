#!/usr/bin/env node
import * as cdk from 'aws-cdk-lib';
import * as lib from '../lib';

const app = new cdk.App();

function setupInfrastructure(app: cdk.App) {
    const dataStack = new lib.DataStack(app, 'DataStack')

    const sqsStack = new lib.SQSStack(app, "SQSStack")

    new lib.LambdasStack(app, 'LambdaStack', {
        dataBucket: dataStack.dataBucket,
        clipsQueue: sqsStack.clipsQueue,
        rawQueue: sqsStack.rawQueue,
        visibilityTimeout: sqsStack.visibilityTimeout,
    })
}

setupInfrastructure(app)
