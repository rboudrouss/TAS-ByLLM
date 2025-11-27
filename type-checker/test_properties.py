import pytest
from hypothesis import given, strategies as st, settings

from mtp_types import *
from expressions import *
from schema import type_to_schema, schema_exists, validate_against_schema
from typechecker import TypeChecker, TypeError
from evaluator import Evaluator, ValidationError

def base_type():
    return st.sampled_from([IntType(), StrType(), BoolType(), FloatType(), NoneType()])

@st.composite
def random_type(draw, depth=3):
    if depth <= 0:
        return draw(base_type())
    c = draw(st.integers(0, 2))
    if c == 0:
        return draw(base_type())
    elif c == 1:
        return ListType(draw(random_type(depth=depth-1)))
    else:
        n = draw(st.integers(1, 3))
        fields = {f"f{i}": draw(random_type(depth=depth-1)) for i in range(n)}
        return RecordType.from_dict(fields)

# lemme 1: totalite
class TestTotality:
    def test_base_types_have_schemas(self):
        assert schema_exists(IntType())
        assert schema_exists(StrType())
        assert schema_exists(BoolType())
        assert schema_exists(FloatType())
        assert schema_exists(NoneType())

    def test_list_type_has_schema(self):
        assert schema_exists(ListType(IntType()))
        assert schema_exists(ListType(ListType(StrType())))

    def test_record_type_has_schema(self):
        r = RecordType.from_dict({"name": StrType(), "age": IntType()})
        assert schema_exists(r)

    def test_function_type_no_schema(self):
        assert not schema_exists(FunctionType(IntType(), StrType()))

    @given(random_type())
    @settings(max_examples=50)
    def test_property_all_json_types_have_schemas(self, t):
        if is_json_serializable_type(t):
            assert schema_exists(t)

# lemme 2: determinisme
class TestDeterminism:
    def test_same_type_same_schema(self):
        t = RecordType.from_dict({"x": IntType(), "y": ListType(StrType())})
        assert type_to_schema(t) == type_to_schema(t)

    @given(random_type())
    @settings(max_examples=50)
    def test_property_determinism(self, t):
        if schema_exists(t):
            assert type_to_schema(t) == type_to_schema(t)

    def test_independent_construction_same_schema(self):
        t1 = ListType(IntType())
        t2 = ListType(IntType())
        assert t1 == t2
        assert type_to_schema(t1) == type_to_schema(t2)

# lemme 3: soundness validation
class TestSoundnessValidation:
    def test_int_validation(self):
        s = type_to_schema(IntType())
        assert validate_against_schema(42, s)
        assert not validate_against_schema("nope", s)

    def test_string_validation(self):
        s = type_to_schema(StrType())
        assert validate_against_schema("hello", s)
        assert not validate_against_schema(123, s)

    def test_list_validation(self):
        s = type_to_schema(ListType(IntType()))
        assert validate_against_schema([1,2,3], s)
        assert not validate_against_schema(["a"], s)

    def test_record_validation(self):
        rt = RecordType.from_dict({"name": StrType(), "age": IntType()})
        s = type_to_schema(rt)
        assert validate_against_schema({"name": "Alice", "age": 30}, s)
        assert not validate_against_schema({"name": "Alice"}, s)

# lemme 4: uniformite TODO
class TestUniformity:
    def test_byllm_uses_same_schema(self):
        rt = RecordType.from_dict({"result": IntType()})
        assert type_to_schema(rt) == type_to_schema(rt)

# progression
class TestProgression:
    def test_constant_is_value(self):
        assert Const(42, IntType()).is_value()

    def test_lambda_is_value(self):
        assert Lambda("x", IntType(), Var("x")).is_value()

    def test_byllm_is_value(self):
        b = ByLLM(Lambda("x", StrType(), Var("x"), StrType()), "gpt-4")
        assert b.is_value()

    def test_application_can_reduce(self):
        app = App(Lambda("x", IntType(), Var("x")), Const(42, IntType()))
        assert not app.is_value()
        result = Evaluator().evaluate(app)
        assert result.is_value()

    def test_record_with_values_is_value(self):
        r = Record({"a": Const(1, IntType()), "b": Const(2, IntType())})
        assert r.is_value()

    def test_list_with_values_is_value(self):
        l = List([Const(1, IntType()), Const(2, IntType())])
        assert l.is_value()

# preservation
class TestPreservation:
    def test_beta_reduction_preserves_type(self):
        app = App(Lambda("x", IntType(), Var("x")), Const(42, IntType()))
        tc = TypeChecker()
        ev = Evaluator()
        t1 = tc.check(app)
        result = ev.evaluate(app)
        t2 = tc.check(result)
        assert t1 == t2 == IntType()

    def test_byllm_invocation_preserves_type(self):
        byllm = ByLLM(Lambda("x", StrType(), Var("x"), IntType()), "gpt-4")
        app = App(byllm, Const("hello", StrType()))
        tc = TypeChecker()
        ev = Evaluator()
        t1 = tc.check(app)
        result = ev.evaluate(app)
        t2 = tc.check(result)
        assert t1 == t2 == IntType()

# end to end
class TestEndToEndSoundness:
    def test_byllm_end_to_end(self):
        rt = RecordType.from_dict({"lang": StrType(), "confidence": FloatType()})
        byllm = ByLLM(Lambda("text", StrType(), Var("text"), rt), "gpt-4")
        app = App(byllm, Const("Hello", StrType()))
        tc = TypeChecker()
        ev = Evaluator()
        assert tc.check(app) == rt
        result = ev.evaluate(app)
        assert tc.check(result) == rt

    def test_invalid_llm_output_raises_validation_error(self):
        def bad_llm(m, f, i, s): return '{"wrong": "stuff"}'
        byllm = ByLLM(Lambda("x", StrType(), Var("x"), IntType()), "gpt-4")
        app = App(byllm, Const("test", StrType()))
        with pytest.raises(ValidationError):
            Evaluator(llm_function=bad_llm).evaluate(app)

# T-ByLLM
class TestTByLLMRule:
    def test_byllm_requires_known_model(self):
        b = ByLLM(Lambda("x", StrType(), Var("x"), StrType()), "unknown-model")
        with pytest.raises(TypeError, match="Unknown model"):
            TypeChecker().check(b)

    def test_byllm_requires_return_type_annotation(self):
        b = ByLLM(Lambda("x", StrType(), Var("x")), "gpt-4")
        with pytest.raises(TypeError, match="return type"):
            TypeChecker().check(b)

    def test_byllm_input_must_be_json_serializable(self):
        ft = FunctionType(IntType(), IntType())
        b = ByLLM(Lambda("f", ft, Var("f"), IntType()), "gpt-4")
        with pytest.raises(TypeError, match="cannot be translated"):
            TypeChecker().check(b)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

