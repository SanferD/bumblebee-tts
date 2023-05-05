#!/bin/bash

BUCKET_NAME=$1
DIR=$2 

echo "bucket-name=${BUCKET_NAME}"
echo "data-dir=${DIR}"
read -p "Do you wish to continue? " -r
echo
if [[ $REPLY =~ ^[Nn]$ ]]
then
    exit 1
fi


for filepath in $(find $DIR -type f); do
    filename=$(basename $filepath)
    echo aws s3 cp $filepath "s3://$BUCKET_NAME/raw/$filename"
    aws s3 cp $filepath "s3://$BUCKET_NAME/raw/$filename"
done

