# types pour MTP
from dataclasses import dataclass
from typing import Dict, FrozenSet, Tuple

class MTPType:
    pass

@dataclass(frozen=True)
class IntType(MTPType):
    def __repr__(self): return "int"

@dataclass(frozen=True)
class StrType(MTPType):
    def __repr__(self): return "str"

@dataclass(frozen=True)
class BoolType(MTPType):
    def __repr__(self): return "bool"

@dataclass(frozen=True)
class FloatType(MTPType):
    def __repr__(self): return "float"

@dataclass(frozen=True)
class NoneType(MTPType):
    def __repr__(self): return "None"

@dataclass(frozen=True)
class ListType(MTPType):
    element_type: MTPType
    def __repr__(self): return f"List[{self.element_type}]"

@dataclass(frozen=True)
class RecordType(MTPType):
    fields: FrozenSet[Tuple[str, MTPType]]

    def __repr__(self):
        return "{" + ", ".join(f"{k}: {v}" for k,v in sorted(self.fields)) + "}"

    def get_field_type(self, label):
        for l, t in self.fields:
            if l == label: return t
        return None

    @classmethod
    def from_dict(cls, d: Dict[str, MTPType]):
        return cls(frozenset(d.items()))

@dataclass(frozen=True)
class FunctionType(MTPType):
    param_type: MTPType
    return_type: MTPType
    def __repr__(self): return f"({self.param_type} -> {self.return_type})"

def is_base_type(t):
    return isinstance(t, (IntType, StrType, BoolType, FloatType, NoneType))

def is_json_serializable_type(t):
    if is_base_type(t): return True
    if isinstance(t, ListType): return is_json_serializable_type(t.element_type)
    if isinstance(t, RecordType): return all(is_json_serializable_type(ft) for _, ft in t.fields)
    if isinstance(t, FunctionType): return False
    return False

