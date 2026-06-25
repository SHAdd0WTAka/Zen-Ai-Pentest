"""
Security tests for AgentCoordinatorV3._safe_ast_eval and _evaluate_condition.
Verifies that the eval() replacement is safe and functional.
"""

from agents.agent_coordinator_v3 import AgentCoordinator


def make_coordinator():
    ac = AgentCoordinator.__new__(AgentCoordinator)
    ac._event_handlers = {}
    ac._active_agents = {}
    return ac


# ============================================================================
# Basic Boolean & Logic
# ============================================================================


class TestBasicBoolean:
    def test_true(self):
        ac = make_coordinator()
        assert ac._evaluate_condition("True", {}) is True

    def test_false(self):
        ac = make_coordinator()
        assert ac._evaluate_condition("False", {}) is False

    def test_not_true(self):
        ac = make_coordinator()
        assert ac._evaluate_condition("not True", {}) is False

    def test_not_false(self):
        ac = make_coordinator()
        assert ac._evaluate_condition("not False", {}) is True

    def test_and(self):
        ac = make_coordinator()
        assert ac._evaluate_condition("True and True", {}) is True
        assert ac._evaluate_condition("True and False", {}) is False
        assert ac._evaluate_condition("False and True", {}) is False

    def test_or(self):
        ac = make_coordinator()
        assert ac._evaluate_condition("True or False", {}) is True
        assert ac._evaluate_condition("False or False", {}) is False

    def test_complex_boolean(self):
        ac = make_coordinator()
        assert ac._evaluate_condition("True and not (False or False)", {}) is True
        assert ac._evaluate_condition("(True or False) and not False", {}) is True


# ============================================================================
# Comparisons
# ============================================================================


class TestComparisons:
    def test_gt(self):
        ac = make_coordinator()
        assert ac._evaluate_condition("results.val > 5", {"val": 10}) is True
        assert ac._evaluate_condition("results.val > 5", {"val": 3}) is False

    def test_lt(self):
        ac = make_coordinator()
        assert ac._evaluate_condition("results.val < 5", {"val": 3}) is True
        assert ac._evaluate_condition("results.val < 5", {"val": 10}) is False

    def test_eq(self):
        ac = make_coordinator()
        assert ac._evaluate_condition("results.val == 42", {"val": 42}) is True
        assert ac._evaluate_condition("results.val == 42", {"val": 7}) is False

    def test_neq(self):
        ac = make_coordinator()
        assert ac._evaluate_condition("results.val != 42", {"val": 7}) is True
        assert ac._evaluate_condition("results.val != 42", {"val": 42}) is False

    def test_gte(self):
        ac = make_coordinator()
        assert ac._evaluate_condition("results.val >= 5", {"val": 5}) is True
        assert ac._evaluate_condition("results.val >= 5", {"val": 6}) is True
        assert ac._evaluate_condition("results.val >= 5", {"val": 4}) is False

    def test_lte(self):
        ac = make_coordinator()
        assert ac._evaluate_condition("results.val <= 5", {"val": 5}) is True
        assert ac._evaluate_condition("results.val <= 5", {"val": 4}) is True
        assert ac._evaluate_condition("results.val <= 5", {"val": 6}) is False

    def test_in(self):
        ac = make_coordinator()
        assert ac._evaluate_condition("results.val in results.list", {"val": 2, "list": [1, 2, 3]}) is True
        assert ac._evaluate_condition("results.val in results.list", {"val": 4, "list": [1, 2, 3]}) is False

    def test_not_in(self):
        ac = make_coordinator()
        assert ac._evaluate_condition("results.val not in results.list", {"val": 4, "list": [1, 2, 3]}) is True
        assert ac._evaluate_condition("results.val not in results.list", {"val": 2, "list": [1, 2, 3]}) is False

    def test_chained_comparison(self):
        ac = make_coordinator()
        assert ac._evaluate_condition("1 < results.val < 10", {"val": 5}) is True
        assert ac._evaluate_condition("1 < results.val < 10", {"val": 0}) is False
        assert ac._evaluate_condition("1 < results.val < 10", {"val": 11}) is False


# ============================================================================
# Dict Attribute & Subscript Access
# ============================================================================


class TestDictAccess:
    def test_dict_attribute_lookup(self):
        ac = make_coordinator()
        assert ac._evaluate_condition("len(results.data) > 5", {"data": [1, 2, 3, 4, 5, 6]}) is True
        assert ac._evaluate_condition("len(results.data) == 0", {"data": []}) is True

    def test_nested_dict_attrs(self):
        ac = make_coordinator()
        assert ac._evaluate_condition("results.a.b.c == 3", {"a": {"b": {"c": 3}}}) is True
        assert ac._evaluate_condition("results.a.b.c == 3", {"a": {"b": {"c": 4}}}) is False

    def test_dict_method_get(self):
        ac = make_coordinator()
        assert ac._evaluate_condition('results.d.get("k") == "v"', {"d": {"k": "v"}}) is True
        assert ac._evaluate_condition('results.d.get("k") == "x"', {"d": {"k": "v"}}) is False


# ============================================================================
# Arithmetic
# ============================================================================


class TestArithmetic:
    def test_addition(self):
        ac = make_coordinator()
        assert ac._evaluate_condition("results.val + 1 == 43", {"val": 42}) is True

    def test_subtraction(self):
        ac = make_coordinator()
        assert ac._evaluate_condition("results.val - 1 == 41", {"val": 42}) is True

    def test_multiplication(self):
        ac = make_coordinator()
        assert ac._evaluate_condition("results.val * 2 == 84", {"val": 42}) is True

    def test_division(self):
        ac = make_coordinator()
        assert ac._evaluate_condition("results.val / 2 == 21.0", {"val": 42}) is True

    def test_floor_division(self):
        ac = make_coordinator()
        assert ac._evaluate_condition("results.val // 2 == 21", {"val": 43}) is True

    def test_modulo(self):
        ac = make_coordinator()
        assert ac._evaluate_condition("results.val % 2 == 1", {"val": 43}) is True

    def test_power(self):
        ac = make_coordinator()
        assert ac._evaluate_condition("results.val ** 2 == 16", {"val": 4}) is True


# ============================================================================
# Built-in Functions (allowed subset)
# ============================================================================


class TestAllowedFunctions:
    def test_len(self):
        ac = make_coordinator()
        assert ac._evaluate_condition("len(results.elements) > 3", {"elements": [1, 2, 3, 4]}) is True
        assert ac._evaluate_condition("len(results.elements) == 0", {"elements": []}) is True

    def test_str(self):
        ac = make_coordinator()
        assert ac._evaluate_condition('str(results.code) == "42"', {"code": 42}) is True

    def test_int(self):
        ac = make_coordinator()
        assert ac._evaluate_condition("int(results.val) == 42", {"val": "42"}) is True

    def test_float(self):
        ac = make_coordinator()
        assert ac._evaluate_condition("float(results.val) == 3.14", {"val": "3.14"}) is True

    def test_bool(self):
        ac = make_coordinator()
        assert ac._evaluate_condition("bool(results.flag)", {"flag": 1}) is True
        assert ac._evaluate_condition("bool(results.flag)", {"flag": 0}) is False

    def test_list(self):
        ac = make_coordinator()
        assert ac._evaluate_condition("results.val == ['a', 'b', 'c']", {}) is False
        assert ac._evaluate_condition("list(results.elements)", {"elements": [1, 2]}) is True
        assert ac._evaluate_condition("list(results.elements)", {"elements": []}) is False

    def test_sum(self):
        ac = make_coordinator()
        assert ac._evaluate_condition("sum(results.nums) > 10", {"nums": [5, 6, 7]}) is True
        assert ac._evaluate_condition("sum(results.nums) == 1", {"nums": [1]}) is True

    def test_min_max(self):
        ac = make_coordinator()
        assert ac._evaluate_condition("min(results.nums) == 1", {"nums": [3, 1, 4, 2]}) is True
        assert ac._evaluate_condition("max(results.nums) == 4", {"nums": [3, 1, 4, 2]}) is True

    def test_abs(self):
        ac = make_coordinator()
        assert ac._evaluate_condition("abs(results.val) == 42", {"val": -42}) is True

    def test_sorted(self):
        ac = make_coordinator()
        assert ac._evaluate_condition("sorted(results.nums) == [1, 2, 3]", {"nums": [3, 1, 2]}) is True

    def test_enumerate_zip(self):
        ac = make_coordinator()
        assert ac._evaluate_condition("list(enumerate(results.elements))", {"elements": ["a", "b"]}) is True
        assert ac._evaluate_condition("list(zip(results.a, results.b))", {"a": [1, 2], "b": [3, 4]}) is True


# ============================================================================
# SECURITY: Dangerous expressions MUST be rejected
# ============================================================================


class TestSecurityRejections:
    def test_block_import(self):
        ac = make_coordinator()
        assert ac._evaluate_condition("import os", {}) is False

    def test_block_import_as(self):
        ac = make_coordinator()
        assert ac._evaluate_condition("import os as os2", {}) is False

    def test_block_from_import(self):
        ac = make_coordinator()
        assert ac._evaluate_condition("from os import system", {}) is False

    def test_block_import_call(self):
        ac = make_coordinator()
        assert ac._evaluate_condition('__import__("os")', {}) is False

    def test_block_dunder_attribute(self):
        ac = make_coordinator()
        assert ac._evaluate_condition("results.__class__", {}) is False

    def test_block_dunder_getattr(self):
        ac = make_coordinator()
        assert ac._evaluate_condition('getattr(results, "__class__")', {}) is False

    def test_block_dunder_init(self):
        ac = make_coordinator()
        assert ac._evaluate_condition('getattr(results, "__init__")', {}) is False

    def test_block_dunder_spec(self):
        ac = make_coordinator()
        assert ac._evaluate_condition("results.__spec__", {}) is False

    def test_block_subclass_hierarchy(self):
        ac = make_coordinator()
        assert ac._evaluate_condition("type(results).__subclasses__()", {}) is False

    def test_block_open(self):
        ac = make_coordinator()
        assert ac._evaluate_condition('open("/etc/passwd")', {}) is False

    def test_block_eval(self):
        ac = make_coordinator()
        assert ac._evaluate_condition('eval("1+1")', {}) is False

    def test_block_exec(self):
        ac = make_coordinator()
        assert ac._evaluate_condition('exec("pass")', {}) is False

    def test_block_compile(self):
        ac = make_coordinator()
        assert ac._evaluate_condition('compile("1+1", "", "eval")', {}) is False

    def test_block_forbidden_method_call(self):
        ac = make_coordinator()
        assert ac._evaluate_condition("results.x.popitem()", {"x": {}}) is False

    def test_block_subprocess_call(self):
        ac = make_coordinator()
        assert ac._evaluate_condition('subprocess.run(["ls"])', {}) is False

    def test_invalid_syntax_returns_false(self):
        ac = make_coordinator()
        assert ac._evaluate_condition("invalid syntax {{{", {}) is False

    def test_divide_by_zero_returns_false(self):
        ac = make_coordinator()
        assert ac._evaluate_condition("1/0", {}) is False

    def test_unknown_variable_returns_false(self):
        ac = make_coordinator()
        assert ac._evaluate_condition("some_unknown_var == 42", {}) is False

    def test_none_comparison(self):
        ac = make_coordinator()
        assert ac._evaluate_condition("results.val is None", {"val": None}) is True
        assert ac._evaluate_condition("results.val is None", {"val": 42}) is False
        assert ac._evaluate_condition("results.val is not None", {"val": 42}) is True
        assert ac._evaluate_condition("results.val is not None", {"val": None}) is False


# ============================================================================
# Edge Cases
# ============================================================================


class TestEdgeCases:
    def test_empty_results(self):
        ac = make_coordinator()
        assert ac._evaluate_condition("True", {}) is True
        assert ac._evaluate_condition("False", {}) is False

    def test_missing_key_in_results(self):
        ac = make_coordinator()
        assert ac._evaluate_condition("results.missing_key > 0", {}) is False
        assert ac._evaluate_condition("results.missing_key > 0", {"other_key": 5}) is False

    def test_nested_attribute_chain(self):
        ac = make_coordinator()
        assert ac._evaluate_condition("results.a.b", {"a": {"b": 42}}) is True

    def test_bool_on_dict(self):
        ac = make_coordinator()
        assert ac._evaluate_condition("results.dict_attr", {"dict_attr": {"key": "val"}}) is True
        assert ac._evaluate_condition("results.empty_dict", {"empty_dict": {}}) is False

    def test_bool_on_list(self):
        ac = make_coordinator()
        assert ac._evaluate_condition("results.list_attr", {"list_attr": [1, 2]}) is True
        assert ac._evaluate_condition("results.empty_list", {"empty_list": []}) is False

    def test_string_equals(self):
        ac = make_coordinator()
        assert ac._evaluate_condition('results.name == "test"', {"name": "test"}) is True
        assert ac._evaluate_condition('results.name != "other"', {"name": "test"}) is True
