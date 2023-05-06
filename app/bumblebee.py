import audio_helpers
import logger
import prepare_bumblebee
import pydub
    

log = logger.get_log()


def bumblebee() -> pydub.AudioSegment:
    phrase2audio_segment = prepare_bumblebee.prepare_phrase2audio_segment(load_data=True, save_data=False)

    while True:
        myphrase = input("Enter phrase: ")
        if not myphrase:
            continue
        audio = tts(prepare_bumblebee.normalize_phrase(myphrase), phrase2audio_segment)
        if audio is None:
            log.warn(f"Could not build audio for '{myphrase}'")
        else:
            log.info(f"Built audio for '{myphrase}'")
            audio_helpers.play(audio)


def tts(myphrase: str, phrase2audio_segment: dict) -> pydub.AudioSegment | None:
    if not myphrase:
        return pydub.AudioSegment.empty()

    words = myphrase.split()
    for i in range(1, len(words)+1):
        subphrase = " ".join(words[:i])
        if subphrase in phrase2audio_segment:
            therest = tts(" ".join(words[i:]), phrase2audio_segment)
            if therest is not None:
                return phrase2audio_segment[subphrase] + therest
    return None


if __name__ == "__main__":
    bumblebee()
