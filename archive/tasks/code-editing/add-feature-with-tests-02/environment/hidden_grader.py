"""Hidden grader for the full evaluate() contract (baked at /opt/canonical/, not
visible to the agent at /app). Emits the per-case pass list as JSON.

The visible tests cover valid expressions. The gradient is the malformed-input
-> ValueError rule and a few deeper valid cases: a parser that only handles
well-formed input passes the visible tests but raises the wrong exception type
(IndexError / silently wrong) on malformed input and lands a partial reward.
"""
import json
import sys

sys.path.insert(0, "/app")
try:
    from calc import evaluate
except Exception as e:  # import/syntax error in the agent's file
    print(json.dumps({"_import_error": str(e)}))
    sys.exit(0)

results = {}


def eq(expr, expected):
    try:
        return abs(evaluate(expr) - expected) < 1e-9
    except Exception:
        return False


def raises_value_error(expr):
    try:
        evaluate(expr)
    except ValueError:
        return True
    except Exception:
        return False
    return False


def raises_zero_div(expr):
    try:
        evaluate(expr)
    except ZeroDivisionError:
        return True
    except Exception:
        return False
    return False


# valid (some also visible — kept for self-containment)
results["valid_precedence"] = eq("2 + 3 * 4", 14.0)
results["valid_left_assoc_sub"] = eq("10 - 3 - 2", 5.0)
results["valid_left_assoc_div"] = eq("100 / 5 / 2", 10.0)
results["valid_unary_nested"] = eq("-(3 + 1)", -4.0)
results["valid_unary_in_product"] = eq("2 * -4", -8.0)
results["valid_deep_nesting"] = eq("((1 + 2) * (3 + 4)) - -1", 22.0)
results["valid_decimal_chain"] = eq("1.5 + 2.5 * 2", 6.5)
results["valid_double_unary"] = eq("- -5", 5.0)

# malformed -> ValueError (the discriminator)
results["err_empty"] = raises_value_error("")
results["err_whitespace_only"] = raises_value_error("   ")
results["err_dangling_plus"] = raises_value_error("1 +")
results["err_leading_op"] = raises_value_error("* 3")
results["err_unbalanced_open"] = raises_value_error("(1 + 2")
results["err_unbalanced_close"] = raises_value_error("1 + 2)")
results["err_two_numbers"] = raises_value_error("1 2")
results["err_stray_char"] = raises_value_error("1 + @")
results["err_empty_parens"] = raises_value_error("()")

# division by zero -> ZeroDivisionError (not swallowed, not ValueError)
results["zero_division_raises"] = raises_zero_div("1 / 0")

results = {k: bool(v) for k, v in results.items()}
print(json.dumps(results))
