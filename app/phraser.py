"""
Iterates over all clips in event dict and transcribes them using aws transcribe
"""
import config
import json
import logger
import s3
import sqs
import structlog
import time
import transcribe_helper


MAX_ATTEMPTS = 20
SLEEP_SECONDS = 15


log = logger.get_log()


def handle(event: dict, context: dict) -> None:
    log.info("Received event", _event=event)
    clips_s3 = s3.S3(s3.Namespace.CLIPS)
    phrases_s3 = s3.S3(s3.Namespace.PHRASES)
    transcribe = transcribe_helper.Transcribe()
    clips_queue = sqs.SQS(config.CLIPS_QUEUE_URL)

    for record in event["Records"]:
        log.info("Processing record", record=record)
        body = json.loads(record["body"])
        receipt_handle = record["receiptHandle"]
        clips_s3_path = body["clip_object_key"]
        clips_s3_object_key = s3.S3ObjectKey(s3.Namespace.CLIPS, clips_s3_path)
        with structlog.contextvars.bound_contextvars(clips_s3_object_key=str(clips_s3_object_key),
                                                     receipt_handle=receipt_handle):
            handle_one_clips_s3_path(clips_s3_object_key=clips_s3_object_key, receipt_handle=receipt_handle,
                                     clips_s3=clips_s3, phrases_s3=phrases_s3, clips_queue=clips_queue,
                                     transcribe=transcribe)


def handle_one_clips_s3_path(clips_s3_object_key: s3.S3ObjectKey, receipt_handle: str,
                             clips_s3: s3.S3, phrases_s3: s3.S3, clips_queue: sqs.SQS,
                             transcribe: transcribe_helper.Transcribe):
    job_name = clips_s3_object_key.get_filestem().replace("=", "")

    with structlog.contextvars.bound_contextvars(job_name=job_name):
        log.info("Starting transcription job")
        transcribe.start_transcription_job(job_name=job_name, s3_object_key=clips_s3_object_key)
        log.info("Successful transcription job")

        for attempt in range(1, MAX_ATTEMPTS+1):
            log.info(f"Waiting for job to finish, {attempt}/{MAX_ATTEMPTS} attempts with {SLEEP_SECONDS}s sleep")
            transcribe_job = transcribe.get_transcription_job(job_name)
            if transcribe_job.is_finished():
                break
            time.sleep(SLEEP_SECONDS)
        else:
            log.error("Transcribe job did not complete")
            return

        # don't cleanup jobs that didn't complete, can investigate further and manually delete when done
        if transcribe_job.is_failed():
            log.error(f"The transcription failed, {transcribe_job}")
            return
        elif not transcribe_job.is_completed():
            log.error(f"Transcribe job has unrecognized status, {transcribe_job}")
            return

        transcription = transcribe_job.get_transcript()

        if transcription:
            transcription_object_key = s3.S3ObjectKey.create_object_key(s3.Namespace.PHRASES, transcription)
            with structlog.contextvars.bound_contextvars(transcription_object_key=str(transcription_object_key)):
                log.info("Creating transcription")
                phrases_s3.copy(clips_s3_object_key, transcription_object_key)
                log.info("Created transcription")
        else:
            log.info("No transcription found")

        log.info("Deleting transcribe job")
        transcribe.delete_transcription_job(job_name=job_name)
        log.info("Deleted transcribe job")

    log.info("Deleting clips object")
    clips_s3.remove(clips_s3_object_key)
    log.info("Deleted clips object")

    log.info("Removing message from queue")
    clips_queue.dequeue(receipt_handle)
    log.info("Removed message from queue")



if __name__ == "__main__":
    handle({}, {})
