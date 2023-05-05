import boto3
import json


class SQS:
    def __init__(self, url: str):
        self._url = url
        self._client = boto3.client("sqs")
    
    def enqueue(self, message: dict) -> None:
        self._client.send_message(QueueUrl=self._url, MessageBody=json.dumps(message),)

    def dequeue(self, receipt_handle) -> None:
        self._client.delete_message(QueueUrl=self._url, ReceiptHandle=receipt_handle)

