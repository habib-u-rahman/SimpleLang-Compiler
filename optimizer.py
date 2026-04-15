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
        changed = True
        iterations = 0
        while changed and iterations < 10:
            changed = False
            code, c1 = self._constant_folding(code)
            code, c2 = self._constant_propagation(code)
            code, c3 = self._dead_code_elimination(code)
            code, c4 = self._remove_unreachable(code)
            changed = c1 or c2 or c3 or c4
            iterations += 1
        return code

    def _remove_unreachable(self, code: list[TAC]) -> tuple[list[TAC], bool]:
        changed = False
        new_code = []; skip = False
        for instr in code:
            if instr.op == "label": skip = False
            if not skip: new_code.append(instr)
            if instr.op == "jump": skip = True; changed = True
        return new_code, changed

    def _constant_propagation(self, code: list[TAC]) -> tuple[list[TAC], bool]:
        changed = False
        const_map: dict[str, object] = {}
        for instr in code:
            if instr.op == "assign":
                v = instr.arg1
                if isinstance(v, (int, float, bool)) or (isinstance(v, str) and v.startswith('"')):
                    const_map[instr.result] = v
                elif isinstance(v, str) and v in const_map:
                    const_map[instr.result] = const_map[v]
                else:
                    const_map.pop(instr.result, None)
            elif instr.op in ("binop", "unary"):
                const_map.pop(instr.result, None)

        def _sub(v):
            if isinstance(v, str) and v in const_map:
                return const_map[v]
            return v

        new_code = []
        for instr in code:
            new = TAC(instr.op, instr.result, instr.arg1, instr.arg2)
            if new.op in ("assign", "print", "cjump"):
                old = new.arg1; new.arg1 = _sub(new.arg1)
                if new.arg1 != old: changed = True
            if new.op == "binop":
                op_sym, rhs = new.arg2
                new_lhs = _sub(new.arg1); new_rhs = _sub(rhs)
                if new_lhs != new.arg1 or new_rhs != rhs: changed = True
                new.arg1 = new_lhs; new.arg2 = (op_sym, new_rhs)
            new_code.append(new)
        return new_code, changed

    def _dead_code_elimination(self, code: list[TAC]) -> tuple[list[TAC], bool]:
        def _is_temp(name) -> bool:
            return isinstance(name, str) and name.startswith("t")
        used: set[str] = set()
        for instr in code:
            for val in (instr.arg1, instr.arg2):
                if isinstance(val, str): used.add(val)
                elif isinstance(val, tuple):
                    for v in val:
                        if isinstance(v, str): used.add(v)
        changed = False
        new_code = []
        for instr in code:
            if (instr.op in ("assign", "binop", "unary")
                    and _is_temp(instr.result) and instr.result not in used):
                changed = True
            else:
                new_code.append(instr)
        return new_code, changed

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
