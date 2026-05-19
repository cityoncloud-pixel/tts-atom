from tts_atom.schemas import EMOTION_PRESETS, TTSRequest, apply_emotion


def test_emotion_maps_speed():
    req = TTSRequest(text="hi", emotion="cheerful")
    out = apply_emotion(req)
    assert out.speed == EMOTION_PRESETS["cheerful"]["speed"]


def test_explicit_speed_not_overwritten():
    req = TTSRequest(text="hi", emotion="cheerful", speed=1.5)
    out = apply_emotion(req)
    assert out.speed == 1.5
