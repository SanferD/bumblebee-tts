import io
import pydub.playback


def audio_segment_to_bytesio(audio: pydub.AudioSegment, format: str) -> io.BytesIO:
    data = io.BytesIO()
    audio.export(data, format=format)
    return data


def play(audio: pydub.AudioSegment) -> None:
    pydub.playback.play(audio)

