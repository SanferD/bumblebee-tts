import boto3
import logger
import requests
import s3


COMPLETED = "COMPLETED"
FAILED = "FAILED"


log = logger.get_log()


class TranscribeJob:
    def __init__(self, data):
        self._data = data
        self._transcript = None

    def is_finished(self) -> bool:
        return self.is_completed() or self.is_failed()

    def is_completed(self) -> bool:
        return self.get_status() == COMPLETED

    def is_failed(self) -> bool:
        return self.get_status() == FAILED

    def get_status(self) -> str:
        return self._data["TranscriptionJob"]["TranscriptionJobStatus"]

    def get_transcript(self) -> str:
        if self._transcript is not None:
            return self._transcript

        transcript_url = self._data["TranscriptionJob"]["Transcript"]["TranscriptFileUri"]
        log.info("fetching transcript from transcript url", transcript_url=transcript_url)
        response = requests.get(transcript_url)
        self._transcript = response.json()["results"]["transcripts"][0]["transcript"]
        log.info("successful fetch transcript")
        return self._transcript


class Transcribe:
    def __init__(self):
        self._client = boto3.client("transcribe")

    def start_transcription_job(self, job_name: str, s3_object_key: s3.S3ObjectKey) -> None:
        self._client.start_transcription_job(
            TranscriptionJobName=job_name,
            LanguageCode="en-US",
            Media={
                "MediaFileUri": str(s3_object_key),
            },
        )

    def get_transcription_job(self, job_name: str) -> TranscribeJob:
        response = self._client.get_transcription_job(
            TranscriptionJobName=job_name,
        )
        return TranscribeJob(response)

    def delete_transcription_job(self, job_name: str) -> None:
        self._client.delete_transcription_job(
            TranscriptionJobName=job_name,
        )
