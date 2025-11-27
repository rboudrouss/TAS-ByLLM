from dataclasses import dataclass
from typing import Any, Dict, List as PyList
from mtp_types import MTPType

class Expression:
    def is_value(self): return False

@dataclass
class Var(Expression):
    name: str
    def __repr__(self): return self.name

@dataclass
class Const(Expression):
    value: Any
    type_annotation: MTPType
    def __repr__(self): return f'"{self.value}"' if isinstance(self.value, str) else str(self.value)
    def is_value(self): return True

@dataclass
class Lambda(Expression):
    param_name: str
    param_type: MTPType
    body: Expression
    return_type: MTPType = None
    def __repr__(self): return f"(λ{self.param_name}. {self.body})"
    def is_value(self): return True

@dataclass
class App(Expression):
    func: Expression
    arg: Expression
    def __repr__(self): return f"({self.func} {self.arg})"

@dataclass
class ByLLM(Expression):
    func: Lambda
    model: str
    def __repr__(self): return f"({self.func} by {self.model})"
    def is_value(self): return True

@dataclass
class Record(Expression):
    fields: Dict[str, Expression]
    def __repr__(self): return "{" + ", ".join(f"{k}={v}" for k,v in self.fields.items()) + "}"
    def is_value(self): return all(e.is_value() for e in self.fields.values())

@dataclass
class Proj(Expression):
    record: Expression
    label: str
    def __repr__(self): return f"{self.record}.{self.label}"

@dataclass
class List(Expression):
    elements: PyList[Expression]
    def __repr__(self): return "[" + ", ".join(str(e) for e in self.elements) + "]"
    def is_value(self): return all(e.is_value() for e in self.elements)

