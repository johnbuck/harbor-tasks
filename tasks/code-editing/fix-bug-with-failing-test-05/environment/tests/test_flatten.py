from flatten import flatten


def test_empty():
    assert flatten([]) == []


def test_already_flat():
    assert flatten([1, 2, 3]) == [1, 2, 3]


def test_one_level():
    assert flatten([1, [2, 3], 4]) == [1, 2, 3, 4]


def test_deeply_nested():
    assert flatten([1, [2, [3, [4, 5]]], 6]) == [1, 2, 3, 4, 5, 6]


def test_mixed_types():
    assert flatten(["a", ["b", ["c"]], "d"]) == ["a", "b", "c", "d"]
