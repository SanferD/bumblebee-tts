"""
The Clipper iterates over all files in specified S3 bucket and clips them with lengths
3s, 5s, 7s and offsets of floor(clip-length/2).
"""
from botocore.exceptions import ClientError
import audio_helpers
import config
import json
import logger
import pydub
import s3
import sqs
import structlog
import typing


log = logger.get_log()


def handle(event, context) -> None:
    log.info(f"Received event={event}")

    raw_s3 = s3.S3(s3.Namespace.RAW)
    clips_s3 = s3.S3(s3.Namespace.CLIPS)
    clips_queue = sqs.SQS(config.CLIPS_QUEUE_URL)
    raw_queue = sqs.SQS(config.RAW_QUEUE_URL)

    for record in event["Records"]:
        log.info("Processing record", record=record)
        body = json.loads(record["body"])
        receipt_handle = record["receiptHandle"]
        raw_s3_object_path = body["raw_object_key"]
        raw_s3_object_key = s3.S3ObjectKey(s3.Namespace.CLIPS, raw_s3_object_path)
        with structlog.contextvars.bound_contextvars(raw_s3_object_key=str(raw_s3_object_key),
                                                     receipt_handle=receipt_handle):
            handle_one_raw_object_key(
                raw_s3_object_key=raw_s3_object_key,
                receipt_handle=receipt_handle,
                raw_s3=raw_s3,
                clips_s3=clips_s3,
                raw_queue=raw_queue,
                clips_queue=clips_queue,
            )


def handle_one_raw_object_key(raw_s3_object_key, receipt_handle, raw_s3,
                              clips_s3, raw_queue, clips_queue):
    log.info("Getting raw object")
    raw_object_bytesio = raw_s3.get_object(raw_s3_object_key)
    log.info("Successful get raw object")

    log.info("Converting raw audio to AudioSegment")
    audio = audio_helpers.bytesio_to_audio_segment(raw_object_bytesio, extension=raw_s3_object_key.get_extension())
    log.info("Successful raw audio AudioSegment")

    for (clip_object_key, clip) in generate_audio_clips(raw_s3_object_key.get_filestem(),
                                                        raw_s3_object_key.get_extension(),
                                                        audio):
        with structlog.contextvars.bound_contextvars(clip_object_s3_path=str(clip_object_key)):
            clip_bytesio = audio_helpers.audio_segment_to_bytesio(clip, format=raw_s3_object_key.get_extension())

            log.info("Saving clip")
            clips_s3.save(clip_object_key, clip_bytesio)
            log.info("Successful save clip")

            clips_sqs_message = {"clip_object_key": clip_object_key.get_key()}
            with structlog.contextvars.bound_contextvars(clips_sqs_message=clips_sqs_message):
                log.info("Enqueing clip")
                clips_queue.enqueue(clips_sqs_message)
                log.info("Successful enqueue clip")

    log.info("Removing raw object")
    raw_s3.remove(raw_s3_object_key)
    log.info("Successful remove raw object")

    log.info("Removing message from raw queue")
    raw_queue.dequeue(receipt_handle)
    log.info("Removed message from raw queue")


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

