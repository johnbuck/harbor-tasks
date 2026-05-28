"""Aggregate helpers over geometry shapes."""

from geometry.shapes import Circle, Rectangle


def total_area(shapes):
    total = 0.0
    for s in shapes:
        if isinstance(s, Circle):
            total += s.area()
        elif isinstance(s, Rectangle):
            total += s.area()
    return total
