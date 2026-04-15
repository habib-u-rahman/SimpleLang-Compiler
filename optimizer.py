# optimizer.py — TAC Optimizer: constant folding pass

from __future__ import annotations
from intermediate import TAC


def _is_number(v) -> bool:
    return isinstance(v, (int, float))

def _fold(op: str, a, b):
    if not (_is_number(a) and _is_number(b)):
        return None
    match op:
        case "+":  return a + b
        case "-":  return a - b
        case "*":  return a * b
        case "/":  return a / b if b != 0 else None
        case "%":  return int(a) % int(b) if b != 0 else None
        case "==": return a == b
        case "!=": return a != b
        case "<":  return a < b
        case ">":  return a > b
        case "<=": return a <= b
        case ">=": return a >= b
        case _:    return None


class Optimizer:
    def optimize(self, code: list[TAC]) -> list[TAC]:
        code = list(code)
        code, _ = self._constant_folding(code)
        return code

    def _constant_folding(self, code: list[TAC]) -> tuple[list[TAC], bool]:
        changed = False
        new_code = []
        for instr in code:
            if instr.op == "binop":
                op_sym, rhs = instr.arg2
                folded = _fold(op_sym, instr.arg1, rhs)
                if folded is not None:
                    new_code.append(TAC("assign", result=instr.result, arg1=folded))
                    changed = True; continue
            elif instr.op == "unary":
                if instr.arg1 == "-" and _is_number(instr.arg2):
                    new_code.append(TAC("assign", result=instr.result, arg1=-instr.arg2))
                    changed = True; continue
            new_code.append(instr)
        return new_code, changed

    @staticmethod
    def print_code(code: list[TAC], title: str = "Optimised TAC"):
        print(f"\n===== {title} =====")
        for instr in code: print(instr)
        print("=" * (len(title) + 12) + "\n")
