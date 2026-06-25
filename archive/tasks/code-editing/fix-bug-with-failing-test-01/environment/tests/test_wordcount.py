from wordcount import count_words


def test_empty_string():
    assert count_words("") == 0


def test_whitespace_only():
    assert count_words("   \t\n  ") == 0


def test_single_word():
    assert count_words("hello") == 1


def test_multiple_words():
    assert count_words("hello world foo bar") == 4


def test_leading_and_trailing_whitespace():
    assert count_words("   hello   world   ") == 2
