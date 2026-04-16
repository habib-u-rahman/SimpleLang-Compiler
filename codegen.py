# =============================================================
# codegen.py — Target Code Generator for SimpleLang
#
# Translates optimised TAC into pseudo-assembly (a simple
# stack-based / register-based instruction set):
#
#   LOAD  x          – push value of x onto stack
#   STORE x          – pop stack top → variable x
#   PUSH  <const>    – push a constant
#   ADD / SUB / MUL / DIV / MOD
#   EQ / NEQ / LT / GT / LTE / GTE
#   AND / OR / NOT
#   NEG              – negate top of stack
#   JMP   label      – unconditional jump
#   JIF   label      – jump if top of stack is true  (pop)
#   JIFN  label      – jump if top of stack is false (pop)
#   LABEL label:     – label definition
#   PRINT            – pop and print top of stack
#   HALT             – end of program
# =============================================================

from __future__ import annotations
from dataclasses import dataclass
from intermediate import TAC


@dataclass
class Instruction:
    op: str
    arg: object = None

    def __str__(self):
        if self.arg is not None:
            return f"    {self.op:<8} {self.arg}"
        return f"    {self.op}"


@dataclass
class LabelInstr:
    name: str

    def __str__(self):
        return f"{self.name}:"


# Map TAC binary operator symbols → assembly opcode
OP_TO_OPCODE = {
    "+": "ADD", "-": "SUB", "*": "MUL", "/": "DIV", "%": "MOD",
    "==": "EQ", "!=": "NEQ", "<": "LT", ">": "GT", "<=": "LTE", ">=": "GTE",
    "&&": "AND", "||": "OR",
}


class CodeGenerator:
    """
    Walks the TAC list and emits a list of pseudo-assembly instructions.
    """

    def __init__(self):
        self.instructions: list = []

    def generate(self, tac: list[TAC]) -> list:
        for instr in tac:
            self._gen_instr(instr)
        self.instructions.append(Instruction("HALT"))
        return self.instructions

    # ------------------------------------------------------------------
    # Per-instruction translation
    # ------------------------------------------------------------------

    def _gen_instr(self, instr: TAC):
        match instr.op:
            case "assign":
                self._push_value(instr.arg1)
                self.instructions.append(Instruction("STORE", instr.result))

            case "binop":
                op_sym, rhs = instr.arg2
                self._push_value(instr.arg1)     # push LHS
                self._push_value(rhs)             # push RHS
                opcode = OP_TO_OPCODE.get(op_sym, op_sym.upper())
                self.instructions.append(Instruction(opcode))
                self.instructions.append(Instruction("STORE", instr.result))

            case "unary":
                op_sym = instr.arg1
                self._push_value(instr.arg2)
                if op_sym == "-":
                    self.instructions.append(Instruction("NEG"))
                else:
                    self.instructions.append(Instruction("NOT"))
                self.instructions.append(Instruction("STORE", instr.result))

            case "cjump":
                cond = instr.arg1
                true_lbl, false_lbl = instr.arg2
                self._push_value(cond)
                self.instructions.append(Instruction("JIF",  true_lbl))
                self.instructions.append(Instruction("JMP",  false_lbl))

            case "jump":
                self.instructions.append(Instruction("JMP", instr.arg1))

            case "label":
                self.instructions.append(LabelInstr(instr.result))

            case "print":
                self._push_value(instr.arg1)
                self.instructions.append(Instruction("PRINT"))

    # ------------------------------------------------------------------
    # Helper: push a value or variable reference
    # ------------------------------------------------------------------

    def _push_value(self, val):
        if isinstance(val, str) and not val.startswith('"'):
            # It's a variable / temp name — load from memory
            self.instructions.append(Instruction("LOAD", val))
        else:
            # It's a constant (int, float, bool, or quoted string)
            self.instructions.append(Instruction("PUSH", val))

    # ------------------------------------------------------------------
    # Display / pretty print
    # ------------------------------------------------------------------

    def print_code(self):
        print("\n===== Target Assembly =====")
        for instr in self.instructions:
            print(instr)
        print("===========================\n")

    def write_to_file(self, path: str):
        with open(path, "w") as f:
            for instr in self.instructions:
                f.write(str(instr) + "\n")
        print(f"Assembly written to {path}")


# ------------------------------------------------------------------
# Simple stack-based interpreter (for testing generated code)
# ------------------------------------------------------------------

class VirtualMachine:
    """
    Executes the pseudo-assembly produced by CodeGenerator.
    Useful for end-to-end testing.
    """

    def __init__(self, instructions: list):
        self.instructions = instructions
        # Build label → index map
        self.label_map: dict[str, int] = {}
        for idx, instr in enumerate(instructions):
            if isinstance(instr, LabelInstr):
                self.label_map[instr.name] = idx

    def run(self):
        memory: dict[str, object] = {}
        stack: list = []
        pc = 0

        while pc < len(self.instructions):
            instr = self.instructions[pc]
            pc += 1

            if isinstance(instr, LabelInstr):
                continue

            match instr.op:
                case "PUSH":  stack.append(instr.arg)
                case "LOAD":  stack.append(memory.get(instr.arg, 0))
                case "STORE": memory[instr.arg] = stack.pop()
                case "ADD":
                    b, a = stack.pop(), stack.pop()
                    stack.append(a + b)
                case "SUB":
                    b, a = stack.pop(), stack.pop()
                    stack.append(a - b)
                case "MUL":
                    b, a = stack.pop(), stack.pop()
                    stack.append(a * b)
                case "DIV":
                    b, a = stack.pop(), stack.pop()
                    stack.append(a / b)
                case "MOD":
                    b, a = stack.pop(), stack.pop()
                    stack.append(int(a) % int(b))
                case "EQ":
                    b, a = stack.pop(), stack.pop()
                    stack.append(a == b)
                case "NEQ":
                    b, a = stack.pop(), stack.pop()
                    stack.append(a != b)
                case "LT":
                    b, a = stack.pop(), stack.pop()
                    stack.append(a < b)
                case "GT":
                    b, a = stack.pop(), stack.pop()
                    stack.append(a > b)
                case "LTE":
                    b, a = stack.pop(), stack.pop()
                    stack.append(a <= b)
                case "GTE":
                    b, a = stack.pop(), stack.pop()
                    stack.append(a >= b)
                case "AND":
                    b, a = stack.pop(), stack.pop()
                    stack.append(bool(a) and bool(b))
                case "OR":
                    b, a = stack.pop(), stack.pop()
                    stack.append(bool(a) or bool(b))
                case "NOT":   stack.append(not stack.pop())
                case "NEG":   stack.append(-stack.pop())
                case "JMP":   pc = self.label_map[instr.arg] + 1
                case "JIF":
                    if stack.pop():
                        pc = self.label_map[instr.arg] + 1
                case "JIFN":
                    if not stack.pop():
                        pc = self.label_map[instr.arg] + 1
                case "PRINT": print(stack.pop())
                case "HALT":  break


# ------------------------------------------------------------------
# Quick standalone test
# ------------------------------------------------------------------
if __name__ == "__main__":
    from lexer import Lexer
    from parser import Parser
    from semantic import SemanticAnalyser
    from intermediate import TACGenerator
    from optimizer import Optimizer

    src = """
    int x = 10;
    int y = x + 5;
    if (x > 5) {
        print(y);
    } else {
        print(x);
    }
    """
    tokens  = Lexer(src).tokenize()
    ast     = Parser(tokens).parse()
    SemanticAnalyser().analyse(ast)
    tac     = TACGenerator().generate(ast)
    opt_tac = Optimizer().optimize(tac)

    cg = CodeGenerator()
    asm = cg.generate(opt_tac)
    cg.print_code()

    print("--- VM Output ---")
    VirtualMachine(asm).run()
