"""
The Clipper iterates over all files in specified S3 bucket and clips them with lengths
3s, 5s, 7s and offsets of floor(clip-length/2).
"""
import audio_helpers
import config
import logger
import pydub
import s3
import structlog
import typing
import sqs
from botocore.exceptions import ClientError


log = logger.get_log()


def handle(event, context) -> None:
    log.info(f"Received event={event}")

    raw_s3 = s3.S3(s3.Namespace.RAW)
    clips_s3 = s3.S3(s3.Namespace.CLIPS)
    clips_queue = sqs.SQS(config.CLIPS_QUEUE_URL)

    for raw_object_key in raw_s3.list_object_keys():
        with structlog.contextvars.bound_contextvars(raw_object_s3_path=str(raw_object_key)):
            try:
                handle_one_raw_object(raw_s3=raw_s3, clips_s3=clips_s3, clips_queue=clips_queue, raw_object_key=raw_object_key)
            except ClientError:
                log.exception("ClientError when handling raw object", exc_info=True)


def handle_one_raw_object(raw_s3: s3.S3, clips_s3: s3.S3, clips_queue: sqs.SQS, raw_object_key: s3.S3ObjectKey) -> None:
    log.info("Getting object")
    raw_object_bytesio = raw_s3.get_object(raw_object_key)
    log.info("Successful get object")

    log.info("Converting to AudioSegment")
    audio = pydub.AudioSegment.from_file(raw_object_bytesio, format=raw_object_key.get_extension())
    log.info("Successful AudioSegment")

    for (clip_object_key, clip) in generate_audio_clips(raw_object_key.get_filestem(),
                                                        raw_object_key.get_extension(),
                                                        audio):
        with structlog.contextvars.bound_contextvars(clip_object_s3_path=str(clip_object_key)):
            clip_bytesio = audio_helpers.audio_segment_to_bytesio(clip, format=raw_object_key.get_extension())

            log.info("Saving clip")
            clips_s3.save(clip_object_key, clip_bytesio)
            log.info("Successful save clip")

            clips_sqs_message = {"clip_object_key": clip_object_key.get_key()}
            with structlog.contextvars.bound_contextvars(clips_sqs_message=clips_sqs_message):
                log.info("Enqueing clip")
                clips_queue.enqueue(clips_sqs_message)
                log.info("Successful enqueue clip")

    log.info("Removing object")
    raw_s3.remove(raw_object_key)
    log.info("Successful remove object")


def generate_audio_clips(filestem: str, extension: str, audio: pydub.AudioSegment) -> typing.Generator[
                                                                                        typing.Tuple[s3.S3ObjectKey,
                                                                                                     pydub.AudioSegment],
                                                                                        None,
                                                                                        None]:
    INTERVALS = [1200, 1500, 2000, 2500, 3000,]
    for interval in INTERVALS:
        for offset in range(0, len(audio), interval//2):
            clip = audio[offset:offset+interval]
            if len(clip) == interval:
                clip_filename = f"{filestem}_offset={offset}ms_interval={interval}ms.{extension}"
                clip_object_key = s3.S3ObjectKey.create_object_key(s3.Namespace.CLIPS, clip_filename)
                yield (clip_object_key, clip)


if __name__ == "__main__":
    handle(None, None)

