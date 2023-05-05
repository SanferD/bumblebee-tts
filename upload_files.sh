#!/bin/bash

BUCKET_NAME=$1
DIR=$2 

for filepath in $(find $DIR -type f); do
    filename=$(basename $filepath)
    echo aws s3 cp $filepath "s3://$BUCKET_NAME/raw/$filename"
    aws s3 cp $filepath "s3://$BUCKET_NAME/raw/$filename"
done

