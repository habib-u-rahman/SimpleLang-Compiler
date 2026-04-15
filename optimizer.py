# =============================================================
# optimizer.py — TAC Optimizer for SimpleLang
#
# Optimisation passes (applied in order):
#   1. Constant Folding   — evaluate constant expressions at
#                           compile time  (e.g. t0 = 3 + 4  → t0 = 7)
#   2. Constant Propagation — replace temps that hold a known
#                           constant with the constant itself
#   3. Dead Code Elimination — remove assignments to temps that
#                           are never subsequently read
#   4. Unreachable Code  — remove instructions after an
#                          unconditional jump up to the next label
# =============================================================

from __future__ import annotations
from intermediate import TAC


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _is_number(v) -> bool:
    return isinstance(v, (int, float))

def _is_bool(v) -> bool:
    return isinstance(v, bool)

def _is_const(v) -> bool:
    return _is_number(v) or _is_bool(v) or isinstance(v, str) and v.startswith('"')

def _fold(op: str, a, b):
    """Try to fold a binary operation at compile-time. Returns None if not foldable."""
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


# ------------------------------------------------------------------
# Optimiser
# ------------------------------------------------------------------

class Optimizer:
    """
    Applies a series of local optimisation passes over a TAC list.
    Call optimize(code) → returns the optimised TAC list.
    """

    def optimize(self, code: list[TAC]) -> list[TAC]:
        code = list(code)   # work on a copy
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

    # ------------------------------------------------------------------
    # Pass 1 — Constant Folding
    # ------------------------------------------------------------------

    def _constant_folding(self, code: list[TAC]) -> tuple[list[TAC], bool]:
        changed = False
        new_code = []
        for instr in code:
            if instr.op == "binop":
                # arg2 is (operator_symbol, right_operand)
                op_sym, rhs = instr.arg2
                lhs = instr.arg1
                folded = _fold(op_sym, lhs, rhs)
                if folded is not None:
                    new_code.append(TAC("assign", result=instr.result, arg1=folded))
                    changed = True
                    continue
            elif instr.op == "unary":
                op_sym = instr.arg1
                operand = instr.arg2
                if op_sym == "-" and _is_number(operand):
                    new_code.append(TAC("assign", result=instr.result, arg1=-operand))
                    changed = True
                    continue
                if op_sym == "!" and isinstance(operand, bool):
                    new_code.append(TAC("assign", result=instr.result, arg1=not operand))
                    changed = True
                    continue
            new_code.append(instr)
        return new_code, changed

    # ------------------------------------------------------------------
    # Pass 2 — Constant Propagation
    # ------------------------------------------------------------------

    def _constant_propagation(self, code: list[TAC]) -> tuple[list[TAC], bool]:
        """
        Track temps/variables assigned a single constant value and substitute
        their uses.  We stop propagating a variable the moment it is
        reassigned.
        """
        changed = False
        # Build propagation map: name -> constant value
        const_map: dict[str, object] = {}
        for instr in code:
            if instr.op == "assign" and _is_const(instr.arg1):
                const_map[instr.result] = instr.arg1
            elif instr.op == "assign" and isinstance(instr.arg1, str):
                # assigned from another var — chain-propagate
                if instr.arg1 in const_map:
                    const_map[instr.result] = const_map[instr.arg1]
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
            if new.op in ("assign", "print", "cjump", "jump"):
                old = new.arg1
                new.arg1 = _sub(new.arg1)
                if new.arg1 != old:
                    changed = True
            if new.op == "binop":
                op_sym, rhs = new.arg2
                new_rhs = _sub(rhs)
                new_lhs = _sub(new.arg1)
                if new_lhs != new.arg1 or new_rhs != rhs:
                    changed = True
                new.arg1 = new_lhs
                new.arg2 = (op_sym, new_rhs)
            if new.op == "unary":
                new_operand = _sub(new.arg2)
                if new_operand != new.arg2:
                    changed = True
                new.arg2 = new_operand
            new_code.append(new)

        return new_code, changed

    # ------------------------------------------------------------------
    # Pass 3 — Dead Code Elimination
    # ------------------------------------------------------------------

    def _dead_code_elimination(self, code: list[TAC]) -> tuple[list[TAC], bool]:
        """Remove assignments to temporary variables (t0, t1 …) that are
        never used as arguments in any subsequent instruction."""

        def _is_temp(name) -> bool:
            return isinstance(name, str) and name.startswith("t")

        # Collect all arg references
        used: set[str] = set()
        for instr in code:
            for val in (instr.arg1, instr.arg2):
                if isinstance(val, str):
                    used.add(val)
                elif isinstance(val, tuple):
                    for v in val:
                        if isinstance(v, str):
                            used.add(v)

        changed = False
        new_code = []
        for instr in code:
            if (instr.op in ("assign", "binop", "unary")
                    and _is_temp(instr.result)
                    and instr.result not in used):
                changed = True   # drop this dead assignment
            else:
                new_code.append(instr)
        return new_code, changed

    # ------------------------------------------------------------------
    # Pass 4 — Remove Unreachable Code
    # ------------------------------------------------------------------

    def _remove_unreachable(self, code: list[TAC]) -> tuple[list[TAC], bool]:
        """Drop instructions between an unconditional jump and the next label."""
        changed = False
        new_code = []
        skip = False
        for instr in code:
            if instr.op == "label":
                skip = False
            if not skip:
                new_code.append(instr)
            if instr.op == "jump":
                skip = True
                changed = True   # we might remove something on a future instr
        return new_code, changed

    # ------------------------------------------------------------------
    # Display
    # ------------------------------------------------------------------

    @staticmethod
    def print_code(code: list[TAC], title: str = "Optimised TAC"):
        print(f"\n===== {title} =====")
        for instr in code:
            print(instr)
        print("=" * (len(title) + 12) + "\n")


# ------------------------------------------------------------------
# Quick standalone test
# ------------------------------------------------------------------
if __name__ == "__main__":
    from lexer import Lexer
    from parser import Parser
    from semantic import SemanticAnalyser
    from intermediate import TACGenerator

    src = """
    int x = 3 + 4;
    int y = x * 2;
    if (x > 5) {
        print(y);
    }
    """
    tokens = Lexer(src).tokenize()
    ast    = Parser(tokens).parse()
    SemanticAnalyser().analyse(ast)
    tac    = TACGenerator().generate(ast)

    print("\n--- Before optimisation ---")
    for i in tac:
        print(i)

    opt = Optimizer()
    optimised = opt.optimize(tac)
    opt.print_code(optimised)
