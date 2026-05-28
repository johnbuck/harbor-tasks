from palindrome import is_palindrome


def test_simple_true():
    assert is_palindrome("racecar") is True


def test_simple_false():
    assert is_palindrome("hello") is False


def test_empty_is_palindrome():
    assert is_palindrome("") is True


def test_ignores_case_and_spaces():
    assert is_palindrome("A man a plan a canal Panama") is True


def test_ignores_punctuation():
    assert is_palindrome("Was it a car or a cat I saw?") is True
