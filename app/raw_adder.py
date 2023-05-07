import config
import logger
import s3
import sqs
import structlog


log = logger.get_log()


def handle(event: dict, context: dict) -> None:

    raw_s3 = s3.S3(s3.Namespace.RAW)
    raw_queue = sqs.SQS(config.RAW_QUEUE_URL)

    for raw_object_key in raw_s3.list_object_keys():
        raw_sqs_message = {"raw_object_key": raw_object_key.get_key()}
        with structlog.contextvars.bound_contextvars(raw_sqs_message=raw_sqs_message):
            log.info("Enqueing raw object key")
            raw_queue.enqueue(raw_sqs_message)
            log.info("Successful enqueue raw object key")


if __name__ == "__main__":
    pass
