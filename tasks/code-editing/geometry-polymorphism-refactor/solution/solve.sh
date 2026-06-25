#!/bin/bash
# Reference solution — adds Triangle (exported from the package both ways) and
# refactors total_area to a polymorphic sum over .area() with NO isinstance
# dispatch and no dead imports. Scores 1.0.
set -e

cat > /app/geometry/shapes.py <<'EOF'
"""Shape classes."""

import math


class Circle:
    def __init__(self, radius):
        self.radius = radius

    def area(self):
        return math.pi * self.radius ** 2


class Rectangle:
    def __init__(self, width, height):
        self.width = width
        self.height = height

    def area(self):
        return self.width * self.height


class Triangle:
    def __init__(self, base, height):
        self.base = base
        self.height = height

    def area(self):
        return 0.5 * self.base * self.height
EOF

cat > /app/geometry/__init__.py <<'EOF'
from geometry.shapes import Circle, Rectangle, Triangle

__all__ = ["Circle", "Rectangle", "Triangle"]
EOF

cat > /app/main.py <<'EOF'
"""Aggregate helpers over geometry shapes."""


def total_area(shapes):
    return sum(s.area() for s in shapes)
EOF
