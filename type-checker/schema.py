# traduction type -> json schema
import jsonschema
from mtp_types import *

class SchemaTranslationError(Exception):
    pass

def type_to_schema(t):
    """convertit un type MTP en json schema"""
    if isinstance(t, IntType): return {"type": "integer"}
    if isinstance(t, StrType): return {"type": "string"}
    if isinstance(t, BoolType): return {"type": "boolean"}
    if isinstance(t, FloatType): return {"type": "number"}
    if isinstance(t, NoneType): return {"type": "null"}

    if isinstance(t, ListType):
        return {"type": "array", "items": type_to_schema(t.element_type)}

    if isinstance(t, RecordType):
        props = {}
        req = []
        for label, ft in sorted(t.fields):
            props[label] = type_to_schema(ft)
            req.append(label)
        return {"type": "object", "properties": props, "required": req, "additionalProperties": False}

    if isinstance(t, FunctionType):
        raise SchemaTranslationError(f"can't serialize function type {t}")

    raise SchemaTranslationError(f"unknown type {t}")

def schema_exists(t):
    try:
        type_to_schema(t)
        return True
    except:
        return False

def validate_against_schema(value, schema):
    try:
        jsonschema.validate(value, schema)
        return True
    except:
        return False

