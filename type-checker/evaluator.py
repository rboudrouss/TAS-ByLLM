# evaluateur MTP - semantique operationnelle
import json
from mtp_types import *
from expressions import *
from schema import type_to_schema, validate_against_schema

class ValidationError(Exception):
    pass

class EvaluationError(Exception):
    pass

def mock_llm(model, func, input_val, schema):
    """fake llm qui genere du json valide"""
    def gen(s):
        t = s.get("type")
        if t == "integer": return 42
        if t == "string": return "generated"
        if t == "boolean": return True
        if t == "number": return 3.14
        if t == "null": return None
        if t == "array": return [gen(s.get("items", {})) for _ in range(2)]
        if t == "object": return {k: gen(v) for k,v in s.get("properties", {}).items()}
        return None
    return json.dumps(gen(schema))

class Evaluator:
    def __init__(self, llm_function=None):
        self.llm = llm_function or mock_llm
        self.steps = 0

    def evaluate(self, expr):
        self.steps = 0
        curr = expr
        while not curr.is_value():
            if self.steps > 1000:
                raise EvaluationError("too many steps")
            next = self.step(curr)
            if next == curr:
                raise EvaluationError(f"stuck: {curr}")
            curr = next
            self.steps += 1
        return curr

    def step(self, expr):
        if expr.is_value(): return expr

        if isinstance(expr, App):
            # reduce func first
            if not expr.func.is_value():
                return App(self.step(expr.func), expr.arg)
            # then arg
            if not expr.arg.is_value():
                return App(expr.func, self.step(expr.arg))
            # beta-byllm
            if isinstance(expr.func, ByLLM):
                return self._invoke_llm(expr.func, expr.arg)
            # beta normal
            if isinstance(expr.func, Lambda):
                return self._subst(expr.func.body, expr.func.param_name, expr.arg)
            raise EvaluationError("can't apply")

        if isinstance(expr, Record):
            new = {}
            done = False
            for k, v in expr.fields.items():
                if not done and not v.is_value():
                    new[k] = self.step(v)
                    done = True
                else:
                    new[k] = v
            return Record(new)

        if isinstance(expr, List):
            new = []
            done = False
            for e in expr.elements:
                if not done and not e.is_value():
                    new.append(self.step(e))
                    done = True
                else:
                    new.append(e)
            return List(new)

        if isinstance(expr, Proj):
            if not expr.record.is_value():
                return Proj(self.step(expr.record), expr.label)
            if isinstance(expr.record, Record):
                return expr.record.fields[expr.label]
            raise EvaluationError("proj on non-record")

        return expr

    def _invoke_llm(self, byllm, arg):
        input_val = self._to_val(arg)
        ret_type = byllm.func.return_type
        schema = type_to_schema(ret_type)

        result = self.llm(byllm.model, byllm.func, input_val, schema)

        try:
            parsed = json.loads(result)
        except:
            raise ValidationError("invalid json from llm")

        if not validate_against_schema(parsed, schema):
            raise ValidationError(f"LLM output {parsed} does not match schema {schema}")

        return self._from_val(parsed, ret_type)

    def _subst(self, expr, var, val):
        if isinstance(expr, Var):
            return val if expr.name == var else expr
        if isinstance(expr, Const):
            return expr
        if isinstance(expr, Lambda):
            if expr.param_name == var: return expr
            return Lambda(expr.param_name, expr.param_type, self._subst(expr.body, var, val), expr.return_type)
        if isinstance(expr, App):
            return App(self._subst(expr.func, var, val), self._subst(expr.arg, var, val))
        if isinstance(expr, ByLLM):
            if expr.func.param_name == var: return expr
            return ByLLM(Lambda(expr.func.param_name, expr.func.param_type,
                               self._subst(expr.func.body, var, val), expr.func.return_type), expr.model)
        if isinstance(expr, Record):
            return Record({k: self._subst(v, var, val) for k,v in expr.fields.items()})
        if isinstance(expr, List):
            return List([self._subst(e, var, val) for e in expr.elements])
        if isinstance(expr, Proj):
            return Proj(self._subst(expr.record, var, val), expr.label)
        return expr

    def _to_val(self, expr):
        if isinstance(expr, Const): return expr.value
        if isinstance(expr, Record): return {k: self._to_val(v) for k,v in expr.fields.items()}
        if isinstance(expr, List): return [self._to_val(e) for e in expr.elements]
        raise EvaluationError("not a value")

    def _from_val(self, val, typ):
        if isinstance(typ, IntType): return Const(val, IntType())
        if isinstance(typ, StrType): return Const(val, StrType())
        if isinstance(typ, BoolType): return Const(val, BoolType())
        if isinstance(typ, FloatType): return Const(val, FloatType())
        if isinstance(typ, NoneType): return Const(None, NoneType())
        if isinstance(typ, ListType): return List([self._from_val(v, typ.element_type) for v in val])
        if isinstance(typ, RecordType):
            return Record({l: self._from_val(val[l], t) for l,t in typ.fields})
        raise EvaluationError("can't convert")

    def _infer_type(self, expr):
        if isinstance(expr, Const): return expr.type_annotation
        return StrType()  # fallback lol

