import json
from mtp_types import *
from expressions import *
from schema import type_to_schema
from typechecker import TypeChecker
from evaluator import Evaluator

def main():
    tc = TypeChecker()
    ev = Evaluator()

    types = [
        IntType(),
        StrType(),
        ListType(IntType()),
        RecordType.from_dict({"name": StrType(), "age": IntType()})
    ]
    for t in types:
        print(f"{t} => {json.dumps(type_to_schema(t))}")

    lam = Lambda("x", IntType(), Var("x"))
    print(f"λx.x : {tc.check(lam)}")

    app = App(lam, Const(42, IntType()))
    print(f"(λx.x) 42 : {tc.check(app)}")

    ret_type = RecordType.from_dict({"sentiment": StrType(), "score": FloatType()})
    byllm = ByLLM(
        Lambda("text", StrType(), Var("text"), ret_type),
        "gpt-4"
    )
    print(f"sentiment_analyzer : {tc.check(byllm)}")

    result = ev.evaluate(app)
    print(f"(λx.x) 42 => {result}")

    expr = App(byllm, Const("I love this!", StrType()))
    result = ev.evaluate(expr)
    print(f"sentiment_analyzer('I love this!') => {result}")

    print(f"\nType preserved: {tc.check(result) == ret_type}")

if __name__ == "__main__":
    main()
