# Bumblebee TTS

This is an app that imitates the Text-To-Speech (TTS) voice of Bumblebee from the Transformers. Here are the steps to run the app:

## How to Run

1. Make sure you have Docker running. Check by typing `docker version`.
2. Configure your AWS account by typing `aws configure`.
3. Navigate to the **infra** folder.
4. Deploy the bootstrap stack by typing `cdk bootstrap`.
5. Deploy all stacks by typing `cdk deploy --all`. You can see any changes made by typing `cdk diff`.
6. Deploy the [ffmpeg AWS Lambda Layer](https://serverlessrepo.aws.amazon.com/applications/us-east-1/145266761615/ffmpeg-lambda-layer) and copy the ARN of the deployed layer.
7. Export the ffmpeg Lambda layer ARN by typing `export FFMPEG_LAYER_ARN=<arn>`.

These steps will deploy the following:

1. DataBucket  
   ![data-bucket](https://user-images.githubusercontent.com/9338001/236513911-374eea6b-463b-4e07-9a28-a9b0adb80a38.png)
2. Lambdas  
   ![lambdas](https://user-images.githubusercontent.com/9338001/236513956-269daa23-1ddb-4ded-b146-79e61e53f242.png)
3. SQS Queue  
   ![sqs](https://user-images.githubusercontent.com/9338001/236513966-0f0bd6e9-7c63-43a1-8d1f-18bc54db5d7a.png)

### Upload the Dataset

To upload the dataset:

1. Use the [voxceleb dataset](https://github.com/clovaai/voxceleb_trainer#dependencies) and follow the instructions in their README to fetch the wav files.
2. Run `./flatten_data.sh <voxceleb-data-dir> <flattened-data-dir>` to create flattened file view of the voxceleb data.
3. Run `./upload_fiels.sh <bucket-name> <flattened-data-dir>` to upload the flattened files to the s3 data bucket.

### Trigger the Clipper

To trigger the clipper:

1. Navigate to AWS Lambda and run the `Clipper` function with any event.
2. The `Clipper` function will clip media files found in `<bucket-name>/raw`, upload the clips to `<bucket-name>/clips`, and add the message to `ClipsQueue`.
3. The `Phraser` Lambda will then process all the messages in the `ClipsQueue`, create transcriptions of the clips using AWS Transcribe, and save the labeled audio clip in `<bucket-name>/phrases`.

You can view the logs to gain further insights during runtime. The phrases will populate inside `<bucket-name>/phrases`.
![phrases](https://user-images.githubusercontent.com/9338001/236521588-c95cf44c-80eb-4f0b-b876-8c43b631eb0e.png)


### Generate Bumblebee Audio

To get started, you'll need to prepare the `phrase2audio_segment.pickle` file. To do this, simply run the command `python prepare_bumblebee.py`. Once that's done, you can run `python bumblebee.py` to execute the program.

```
2023-05-06T15:26:34.699910Z [info     ] Loading phrase2audio_segment
2023-05-06T15:26:34.733416Z [info     ] Loaded phrase2audio_segment    phrases=999
Enter phrase: 
```
https://user-images.githubusercontent.com/9338001/236633206-ef9d7628-b18d-48a4-98e7-25baa99fd693.mp4

### Environment Variables

Here is a user-friendly version of the table:

| Environment Key    | Description | Required |
| :-----: | :-------: | :-------: |
| BUCKET_NAME  | The name of the S3 data bucket created by CDK. | Yes |
| CLIPS_QUEUE_URL | The URL of the SQS queue created by CDK. | Yes |
| DEBUG    | Determines whether to enable DEBUG mode. The default value is to disable it. Use this setting for local development. | No |
| CLIPS_OBJECT_PREFIX | The object prefix for clips. This setting is required if DEBUG is disabled. | Required if DEBUG is disabled |
| PHRASES_OBJECT_PREFIX | The object prefix for phrases. This setting is required if DEBUG is disabled. | Required if DEBUG is disabled |
| RAW_OBJECT_PREFIX | The object prefix for raw data. This setting is required if DEBUG is disabled. | Required if DEBUG is disabled |



