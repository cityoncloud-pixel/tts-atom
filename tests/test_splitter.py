from tts_atom.core.splitter import split_sentences


def test_chinese_multi_sentence():
    text = "好的，我们先看第一题。5加3等于几呢？你可以先数5个，再数3个。"
    parts = split_sentences(text)
    assert len(parts) >= 2


def test_empty():
    assert split_sentences("  ") == []
