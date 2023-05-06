import bumblebee
import config
import pickle
import pydub
import s3
import string


def prepare_phrase2audio_segment(load_data=False, save_data=True) -> dict:
    if load_data:
        with open(config.PHRASE2AUDIO_FILENAME, "rb") as handle:
            phrase2audio_segment = pickle.load(handle)
    else:
        phrases_s3 = s3.S3(s3.Namespace.PHRASES)
        phrase2audio_segment = dict()
        for phrase_s3_object_key in phrases_s3.list_object_keys():
            phrase_bytesio = phrases_s3.get_object(phrase_s3_object_key)
            phrase = bumblebee.normalize_phrase(phrase_s3_object_key.get_filestem())
            phrase2audio_segment[phrase] = pydub.AudioSegment.from_file(phrase_bytesio, format="wav")

        if save_data:
            with open(config.PHRASE2AUDIO_FILENAME, "wb") as handle:
                pickle.dump(phrase2audio_segment, handle, protocol=pickle.HIGHEST_PROTOCOL)

    return phrase2audio_segment


def normalize_phrase(phrase: str) -> None:
    return " ".join(phrase.lower().translate(str.maketrans(" ", " ", string.punctuation)).split())


if __name__ == "__main__":
    prepare_phrase2audio_segment(load_data=False, save_data=True)
