import os


DATA_BUCKET="bumblebee-sanferdsouza"
IS_DEBUG = os.environ.get("DEBUG", "false").lower() == "true"
SQS_URL = "https://sqs.us-east-1.amazonaws.com/180797159824/bumblebee-clips"

