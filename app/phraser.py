import s3
import transcribe_helper
import logger
import structlog
import time


MAX_ATTEMPTS = 20
SLEEP_SECONDS = 15


log = logger.get_log()


def handle(event: dict, context: dict) -> None:
    log.info("Received event", _event=event)
    clips_s3_path = "2.wav"
    clips_s3 = s3.S3(s3.Namespace.CLIPS)
    phrases_s3 = s3.S3(s3.Namespace.PHRASES)
    transcribe = transcribe_helper.Transcribe()
    clips_s3_object_key = s3.S3ObjectKey(s3.Namespace.CLIPS, clips_s3_path)
    with structlog.contextvars.bound_contextvars(clips_s3_object_key=str(clips_s3_object_key)):
        handle_one_clips_s3_path(clips_s3_object_key=clips_s3_object_key, clips_s3=clips_s3,
                                 phrases_s3=phrases_s3, transcribe=transcribe)


def handle_one_clips_s3_path(clips_s3_object_key, clips_s3, phrases_s3, transcribe):
    log.info("Attempting to get object")
    clips_s3_object_bytesio = clips_s3.get_object(clips_s3_object_key)
    log.info("Successful get object")

    job_name = clips_s3_object_key.get_filestem()

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
        transcription_object_key = s3.S3ObjectKey.create_object_key(s3.Namespace.PHRASES, transcription)

    with structlog.contextvars.bound_contextvars(transcription_object_key=str(transcription_object_key)):
        log.info("Saving transcription")
        phrases_s3.save(transcription_object_key, clips_s3_object_bytesio)
        log.info("Saved transcription")

    with structlog.contextvars.bound_contextvars(job_name=job_name):
        log.info("Deleting transcribe job")
        transcribe.delete_transcription_job(job_name=job_name)
        log.info("Deleted transcribe job")


if __name__ == "__main__":
    handle({}, {})
