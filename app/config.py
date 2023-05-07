import os
from botocore.client import Config


IS_DEBUG = os.environ.get("DEBUG", "false").lower() == "true"


def get_env(env_name: str, debug_default=None) -> str:
    value = os.environ.get(env_name, debug_default if IS_DEBUG else None)
    if value is None:
        raise Exception(f"'{env_name}' environment variable is not specified")
    return value


BUCKET_NAME = get_env("BUCKET_NAME")
CLIPS_QUEUE_URL = get_env("CLIPS_QUEUE_URL")
RAW_QUEUE_URL = get_env("RAW_QUEUE_URL")
CLIPS_OBJECT_PREFIX = get_env("CLIPS_OBJECT_PREFIX", debug_default="clips")
PHRASES_OBJECT_PREFIX = get_env("PHRASES_OBJECT_PREFIX", debug_default="phrases")
RAW_OBJECT_PREFIX = get_env("RAW_OBJECT_PREFIX", debug_default="raw")
PHRASE2AUDIO_FILENAME = "../phrase2audio_segment.pickle"

botocore_config = Config(
    connect_timeout=5,
    read_timeout=30,
    max_pool_connections=10,
    retries={'max_attempts': 10},
)
