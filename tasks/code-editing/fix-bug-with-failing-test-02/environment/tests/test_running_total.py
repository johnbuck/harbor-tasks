from running_total import running_total


def test_empty():
    assert running_total([]) == []


def test_single():
    assert running_total([5]) == [5]


def test_basic():
    assert running_total([1, 2, 3]) == [1, 3, 6]


def test_with_negatives():
    assert running_total([3, -1, -1]) == [3, 2, 1]


def test_all_zeros():
    assert running_total([0, 0, 0]) == [0, 0, 0]
