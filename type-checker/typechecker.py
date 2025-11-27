# typechecker MTP
from dataclasses import dataclass, field
from mtp_types import *
from expressions import *
from schema import schema_exists

class TypeError(Exception):
    pass

@dataclass
class TypeContext:
    bindings: dict = field(default_factory=dict)

    def extend(self, name, typ):
        new = self.bindings.copy()
        new[name] = typ
        return TypeContext(new)

    def lookup(self, name):
        return self.bindings.get(name)

@dataclass
class ModelContext:
    models: set = field(default_factory=lambda: {"gpt-4", "gpt-3.5-turbo", "claude-3"})
    def contains(self, m): return m in self.models

class TypeChecker:
    def __init__(self, model_ctx=None):
        self.model_ctx = model_ctx or ModelContext()

    def check(self, expr, ctx=None):
        if ctx is None: ctx = TypeContext()

        # variable
        if isinstance(expr, Var):
            t = ctx.lookup(expr.name)
            if t is None: raise TypeError(f"Unbound variable: {expr.name}")
            return t

        # constante
        if isinstance(expr, Const):
            return expr.type_annotation

        # lambda
        if isinstance(expr, Lambda):
            new_ctx = ctx.extend(expr.param_name, expr.param_type)
            body_t = self.check(expr.body, new_ctx)
            if expr.return_type and expr.return_type != body_t:
                raise TypeError(f"Return type mismatch")
            return FunctionType(expr.param_type, body_t)

        # application
        if isinstance(expr, App):
            ft = self.check(expr.func, ctx)
            if not isinstance(ft, FunctionType):
                raise TypeError(f"Expected function, got {ft}")
            at = self.check(expr.arg, ctx)
            if at != ft.param_type:
                raise TypeError(f"Arg type mismatch")
            return ft.return_type

        # byllm
        if isinstance(expr, ByLLM):
            return self._check_byllm(expr, ctx)

        # record
        if isinstance(expr, Record):
            field_types = {l: self.check(e, ctx) for l, e in expr.fields.items()}
            return RecordType.from_dict(field_types)

        # projection
        if isinstance(expr, Proj):
            rt = self.check(expr.record, ctx)
            if not isinstance(rt, RecordType):
                raise TypeError("Expected record")
            ft = rt.get_field_type(expr.label)
            if ft is None: raise TypeError(f"No field {expr.label}")
            return ft

        # liste
        if isinstance(expr, List):
            if not expr.elements: raise TypeError("Empty list")
            t0 = self.check(expr.elements[0], ctx)
            for e in expr.elements[1:]:
                if self.check(e, ctx) != t0:
                    raise TypeError("List elements must have same type")
            return ListType(t0)

        raise TypeError(f"Unknown expr: {type(expr)}")

    def _check_byllm(self, expr, ctx):
        # T-ByLLM
        if not isinstance(expr.func, Lambda):
            raise TypeError("ByLLM needs lambda")
        if expr.func.return_type is None:
            raise TypeError("ByLLM lambda must have explicit return type annotation")
        if not self.model_ctx.contains(expr.model):
            raise TypeError(f"Unknown model: {expr.model}")

        pt = expr.func.param_type
        rt = expr.func.return_type

        if not schema_exists(pt):
            raise TypeError(f"Input type {pt} cannot be translated to JSON schema")
        if not schema_exists(rt):
            raise TypeError(f"Output type {rt} cannot be translated to JSON schema")

        return FunctionType(pt, rt)

