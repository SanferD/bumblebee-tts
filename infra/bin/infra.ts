#!/usr/bin/env node
import * as cdk from 'aws-cdk-lib';
import * as lib from '../lib';

const app = new cdk.App();

function setupInfrastructure(app: cdk.App) {
    const dataStack = new lib.DataStack(app, 'DataStack');

    new lib.LambdasStack(app, 'LambdaStack', {
        dataBucket: dataStack.dataBucket,
    })
}

setupInfrastructure(app)
