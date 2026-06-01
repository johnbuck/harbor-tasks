"""Hidden grader for the full geometry-refactor contract (baked at
/opt/canonical/, not visible to the agent at /app). Emits the per-case pass list
as JSON.

The visible tests cover Triangle.area, a mixed-known total, and one duck-typed
shape. The gradient cases are the package-level Triangle export, the empty-list
result, the raise-on-non-shape rule, and the "refactor removed isinstance"
behavior — a solution that just appends another isinstance branch in main.py
passes the duck-typed visible test only by luck of summing, but fails the
import-from-package and no-dead-code checks.
"""
import json
import sys

sys.path.insert(0, "/app")

results = {}


def check(name, fn):
    try:
        results[name] = bool(fn())
    except Exception:
        results[name] = False


# 1. Triangle area
def _triangle_area():
    from geometry.shapes import Triangle

    return abs(Triangle(6, 4).area() - 12.0) < 1e-9


check("triangle_area", _triangle_area)


# 2. package-level exports (both import paths)
def _triangle_from_package():
    from geometry import Triangle  # noqa: F401

    return True


check("triangle_exported_from_package", _triangle_from_package)


def _circle_rect_still_exported():
    from geometry import Circle, Rectangle  # noqa: F401

    return True


check("circle_rect_still_exported", _circle_rect_still_exported)


# existing behavior intact
def _circle_intact():
    import math
    from geometry.shapes import Circle

    return abs(Circle(2).area() - math.pi * 4) < 1e-9


check("circle_behavior_intact", _circle_intact)


def _rectangle_intact():
    from geometry.shapes import Rectangle

    return Rectangle(3, 4).area() == 12


check("rectangle_behavior_intact", _rectangle_intact)


# 3. polymorphic total_area over an unknown duck-typed shape
def _polymorphic_unknown():
    from main import total_area

    class Pentagon:
        def area(self):
            return 7.5

    return abs(total_area([Pentagon()]) - 7.5) < 1e-9


check("total_area_polymorphic_unknown", _polymorphic_unknown)


def _mixed_total():
    import math
    from geometry.shapes import Circle, Rectangle, Triangle
    from main import total_area

    shapes = [Rectangle(2, 3), Triangle(4, 2), Circle(1)]  # 6 + 4 + pi
    return abs(total_area(shapes) - (10.0 + math.pi)) < 1e-9


check("total_area_mixed", _mixed_total)


# 4. empty list -> 0.0
def _empty():
    from main import total_area

    return total_area([]) == 0.0


check("total_area_empty_is_zero", _empty)


# 5. raise on a non-shape (no area())
def _raises_on_non_shape():
    from main import total_area

    try:
        total_area([object()])
    except (AttributeError, TypeError):
        return True
    return False


check("total_area_raises_on_non_shape", _raises_on_non_shape)


# refactor quality: main.py no longer dispatches on type
def _no_isinstance_in_main():
    src = open("/app/main.py").read()
    return "isinstance" not in src


check("main_has_no_isinstance", _no_isinstance_in_main)

print(json.dumps(results))
