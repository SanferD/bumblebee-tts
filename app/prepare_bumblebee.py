import config
import logger
import pickle
import pydub
import s3
import string
import structlog


log = logger.get_log()


def prepare_phrase2audio_segment(load_data=False, save_data=True) -> dict:
    if load_data:
        with structlog.contextvars.bound_contextvars(phrase2audio_segment_file=config.PHRASE2AUDIO_FILENAME):
            log.info("Loading phrase2audio_segment")
            with open(config.PHRASE2AUDIO_FILENAME, "rb") as handle:
                phrase2audio_segment = pickle.load(handle)
            log.info("Load phrase2audio_segment successful")
    else:
        log.info("Populating phrase2audio_segment")
        phrases_s3 = s3.S3(s3.Namespace.PHRASES)
        phrase2audio_segment = dict()
        for (i , phrase_s3_object_key) in enumerate(phrases_s3.list_file_object_keys()):
            phrase_bytesio = phrases_s3.get_object_contents(phrase_s3_object_key)
            phrase = normalize_phrase(phrase_s3_object_key.get_filestem())
            phrase2audio_segment[phrase] = pydub.AudioSegment.from_file(phrase_bytesio, format="wav")
            if i > 0 and i%25 == 0:
                log.info(f"Populated {i} phrases so far (unknown out of how many)")
        log.info(f"Populated phrase2audio_segment, {len(phrase2audio_segment)} phrases")

        if save_data:
            with structlog.contextvars.bound_contextvars(phrase2audio_segment_file=config.PHRASE2AUDIO_FILENAME):
                log.info("Saving phrase2audio_segment")
                with open(config.PHRASE2AUDIO_FILENAME, "wb") as handle:
                    pickle.dump(phrase2audio_segment, handle, protocol=pickle.HIGHEST_PROTOCOL)
                log.info("Saved phrase2audio_segment")

    return phrase2audio_segment


def normalize_phrase(phrase: str) -> None:
    return " ".join(phrase.lower().translate(str.maketrans(" ", " ", string.punctuation)).split())


if __name__ == "__main__":
    prepare_phrase2audio_segment(load_data=False, save_data=True)
