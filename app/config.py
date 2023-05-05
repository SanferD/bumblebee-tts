import os


def get_env(env_name: str) -> str:
    if not env_name in os.environ:
        raise Exception(f"'{env_name}' environment variable is not specified")
    return os.environ[env_name]


DATA_BUCKET = get_env("DATA_BUCKET")
CLIPS_QUEUE_URL = get_env("CLIPS_QUEUE_URL")
IS_DEBUG = os.environ.get("DEBUG", "false").lower() == "true"
