import math

from geometry.shapes import Circle, Rectangle, Triangle
from main import total_area


def test_circle_area():
    assert math.isclose(Circle(2).area(), math.pi * 4)


def test_rectangle_area():
    assert Rectangle(3, 4).area() == 12


def test_triangle_area():
    assert math.isclose(Triangle(6, 4).area(), 12.0)


def test_total_area_mixed_known():
    shapes = [Rectangle(2, 3), Triangle(4, 2)]  # 6 + 4
    assert math.isclose(total_area(shapes), 10.0)


def test_total_area_is_polymorphic():
    # A shape type unknown to shapes.py — total_area must duck-type on .area().
    class Square:
        def __init__(self, side):
            self.side = side

        def area(self):
            return self.side * self.side

    assert math.isclose(total_area([Square(3), Rectangle(1, 1)]), 10.0)
