import io
import pydub
import pydub.playback


def bytesio_to_audio_segment(raw_object_bytesio: io.BytesIO, extension: str) -> pydub.AudioSegment:
    return pydub.AudioSegment.from_file(raw_object_bytesio, format=extension)


def audio_segment_to_bytesio(audio: pydub.AudioSegment, format: str) -> io.BytesIO:
    data = io.BytesIO()
    audio.export(data, format=format)
    return data


def play(audio: pydub.AudioSegment) -> None:
    pydub.playback.play(audio)

