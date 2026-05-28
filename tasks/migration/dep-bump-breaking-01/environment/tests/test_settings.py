from settings import AppSettings


def test_defaults():
    s = AppSettings()
    assert s.host == "localhost"
    assert s.port == 8080
