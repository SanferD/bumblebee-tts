# bumblebee

App that attempts to mimic TTS like bumblebee from Transformers

## How to run

Docker needs to be running. Verify via `docker version`.

1. Configure aws via `aws configure`.
1. cd into **infra** folder
1. Deploy bootstrap stack `cdk bootstrap`
1. Deploy all stacks `cdk deploy --all`. Can view changes using `cdk diff`
1. Navigate to AWS Lambda and create the [ffmpeg AWS Lambda Layer](https://serverlessrepo.aws.amazon.com/applications/us-east-1/145266761615/ffmpeg-lambda-layer).
1. Copy the arn of the ffmpeg Lambda layer and export it `export FFMPEG_LAYER_ARN=<arn>`

This would deploy the following:
1. DataBucket
![data-bucket](https://user-images.githubusercontent.com/9338001/236513911-374eea6b-463b-4e07-9a28-a9b0adb80a38.png)
2. Lambdas
![lambdas](https://user-images.githubusercontent.com/9338001/236513956-269daa23-1ddb-4ded-b146-79e61e53f242.png)
3. SQS Queue
![sqs](https://user-images.githubusercontent.com/9338001/236513966-0f0bd6e9-7c63-43a1-8d1f-18bc54db5d7a.png)

### Upload the dataset

I used the [voxceleb dataset](https://github.com/clovaai/voxceleb_trainer#dependencies).
Follow the instructions in their README to fetch the wav files.
Then apply the following steps to process the files and upload them to s3.
1. Run `./flatten_data.sh <voxceleb-data-dir> <flattened-data-dir>`
1. Run `./upload_fiels.sh <bucket-name> <flattened-data-dir>`

### Trigger the clipper

Navigate to AWS Lambda and run the `Clipper` function with any event.
This will clip media files found in `<bucket-name>/raw`, upload the clips to `<bucket-name>/clips`, and add the message to `ClipsQueue`.
The `Phraser` Lambda will then process all the messages in the `ClipsQueue`, create transcriptions of the clips using AWS Transcribe, and save the labeled audio clip in `<bucket-name>/phrases`.
![transcribes](https://user-images.githubusercontent.com/9338001/236515746-cf88f501-cf05-4afc-ae2c-3738873ce87e.png)

View the logs to gain further insights during runtime
![log-events](https://user-images.githubusercontent.com/9338001/236517267-0388192a-e848-4fd9-b0b4-91489dfdf522.png)

The phrases will populate inside `<bucket-name>/phrases`
![phrases](https://user-images.githubusercontent.com/9338001/236517756-3bcccb10-9ff3-455d-81b3-5723f241a282.png)

### Generate bumblebee audio

TODO

