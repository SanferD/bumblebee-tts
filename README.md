# Bumblebee TTS

This is an app that imitates the Text-To-Speech (TTS) voice of Bumblebee from the Transformers. Here are the steps to run the app:

## How to Run

1. Make sure you have Docker running. Check by typing `docker version`.
2. Configure your AWS account by typing `aws configure`.
3. Navigate to the **infra** folder.
4. Deploy the bootstrap stack by typing `cdk bootstrap`.
5. Deploy all stacks by typing `cdk deploy --all`. You can see any changes made by typing `cdk diff`.
6. Deploy the [ffmpeg AWS Lambda Layer](https://serverlessrepo.aws.amazon.com/applications/us-east-1/145266761615/ffmpeg-lambda-layer) and copy the ARN of the deployed layer.
7. Export the ffmpeg Lambda layer ARN by typing `export FFMPEG_LAYER_ARN=<arn>`. This is needed to deploy the cdk stacks.

These steps will deploy the following:

1. DataBucket
![data-bucket](https://user-images.githubusercontent.com/9338001/236513911-374eea6b-463b-4e07-9a28-a9b0adb80a38.png)
2. Lambdas
![lambdas](https://user-images.githubusercontent.com/9338001/236701958-7cdbc523-90c4-41ca-a321-cd30ce8123c2.png)
3. SQS Queue
![sqs](https://user-images.githubusercontent.com/9338001/236701358-e1ca2f15-c37d-4e2e-8859-f316e9accc7b.png)

### Upload the Dataset

To upload the dataset:

1. Use the [voxceleb dataset](https://github.com/clovaai/voxceleb_trainer#dependencies) and follow the instructions in their README to fetch the wav files.
2. Run `./flatten_data.sh <voxceleb-data-dir> <flattened-data-dir>` to create flattened file view of the voxceleb data. Example contents of `<flattened-data-dir>`:
```
Nani Mo Nai ls /mnt/d/data/output/ | head -n 5
10.wav
100.wav
1000.wav
10000.wav
100000.wav
```
3. Run `./upload_files.sh <bucket-name> <flattened-data-dir>` to upload the flattened files to the s3 data bucket.

### Trigger the Data Pipeline

1. Go to AWS Lambda and execute the `RawAdder` function using any event.
2. The `RawAdder` function will look through all object keys in `<bucket-name>/raw`, add the object key to a message, and send it to the `RawQueue`.
3. `RawQueue` will trigger the `Clipper` function for each message. `Clipper` will clip the relevant media file found in `<bucket-name>/raw`, upload the clips to `<bucket-name>/clips`, and add object key to a message to `ClipsQueue`.
4. The `Phraser` Lambda will process all messages in the `ClipsQueue`. It will transcribe the clips using AWS Transcribe and save the labeled audio clip in `<bucket-name>/phrases`.

You can view the logs to gain further insights during runtime. The phrases will populate inside `<bucket-name>/phrases`.
![phrases](https://user-images.githubusercontent.com/9338001/236521588-c95cf44c-80eb-4f0b-b876-8c43b631eb0e.png)

### Generate Bumblebee Audio

To begin, you need to prepare the `phrase2audio_segment.pickle` file. You can do this by running `python prepare_bumblebee.py`, but only after the phrases have been added to the phrases directory. Once prepared, run `python bumblebee.py` to execute the program.

```
2023-05-06T15:26:34.699910Z [info     ] Loading phrase2audio_segment
2023-05-06T15:26:34.733416Z [info     ] Loaded phrase2audio_segment    phrases=999
Enter phrase: 
```
https://user-images.githubusercontent.com/9338001/236633206-ef9d7628-b18d-48a4-98e7-25baa99fd693.mp4

### Environment Variables

#### App

| Environment Key    | Description | Required |
| :-----: | :-------: | :-------: |
| BUCKET_NAME  | The name of the S3 data bucket created by CDK. | Yes |
| CLIPS_QUEUE_URL | The URL of the clips SQS queue created by CDK. | Yes |
| RAW_QUEUE_URL | The URL of the raw SQS queue created by CDK. | Yes |
| DEBUG    | Determines whether to enable DEBUG mode. The default value is to disable it. Use this setting for local development. | No |
| CLIPS_OBJECT_PREFIX | The object prefix for clips. This setting is required if DEBUG is disabled. | Required if DEBUG is disabled |
| PHRASES_OBJECT_PREFIX | The object prefix for phrases. This setting is required if DEBUG is disabled. | Required if DEBUG is disabled |
| RAW_OBJECT_PREFIX | The object prefix for raw data. This setting is required if DEBUG is disabled. | Required if DEBUG is disabled |

#### Infra

| Environment Key    | Description | Required |
| :-----: | :-------: | :-------: |
| FFMPEG_LAYER_ARN  | The ffmpeg Lambda layer arn. | Yes |

