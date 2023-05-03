import structlog
import config


def get_log():
    structlog.configure(
        processors=[
            structlog.processors.EventRenamer("message"),
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.format_exc_info,
            structlog.processors.TimeStamper("iso"),
            structlog.dev.ConsoleRenderer(event_key="message") if config.IS_DEBUG else structlog.processors.JSONRenderer(),
        ],
    )
    log = structlog.get_logger()
    return log


if __name__ == "__main__":
    log = get_log()
    log.info("hello")
    log.info("test")
    log.debug("test")
    try:
        raise Exception("yikes")
    except Exception as e:
        log.exception("oh no", exc_info=True)

