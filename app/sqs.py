import boto3
import json
import config


class SQS:
    def __init__(self, url: str):
        self._url = url
        self._client = boto3.client("sqs", config=config.botocore_config)
    
    def send_message(self, message: dict) -> None:
        self._client.send_message(QueueUrl=self._url, MessageBody=json.dumps(message),)

    def delete_message(self, receipt_handle) -> None:
        self._client.delete_message(QueueUrl=self._url, ReceiptHandle=receipt_handle)

