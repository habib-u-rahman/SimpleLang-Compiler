# codegen.py — Target Code Generator for SimpleLang

from __future__ import annotations
from dataclasses import dataclass
from intermediate import TAC


@dataclass
class Instruction:
    op: str
    arg: object = None
    def __str__(self):
        if self.arg is not None: return f"    {self.op:<8} {self.arg}"
        return f"    {self.op}"


@dataclass
class LabelInstr:
    name: str
    def __str__(self): return f"{self.name}:"


OP_TO_OPCODE = {
    "+": "ADD", "-": "SUB", "*": "MUL", "/": "DIV", "%": "MOD",
    "==": "EQ", "!=": "NEQ", "<": "LT", ">": "GT", "<=": "LTE", ">=": "GTE",
    "&&": "AND", "||": "OR",
}


class CodeGenerator:
    def __init__(self):
        self.instructions: list = []

    def generate(self, tac: list[TAC]) -> list:
        for instr in tac:
            self._gen_instr(instr)
        self.instructions.append(Instruction("HALT"))
        return self.instructions

    def _gen_instr(self, instr: TAC):
        match instr.op:
            case "assign":
                self._push_value(instr.arg1)
                self.instructions.append(Instruction("STORE", instr.result))
            case "binop":
                op_sym, rhs = instr.arg2
                self._push_value(instr.arg1)
                self._push_value(rhs)
                self.instructions.append(Instruction(OP_TO_OPCODE.get(op_sym, op_sym.upper())))
                self.instructions.append(Instruction("STORE", instr.result))
            case "unary":
                self._push_value(instr.arg2)
                self.instructions.append(Instruction("NEG" if instr.arg1 == "-" else "NOT"))
                self.instructions.append(Instruction("STORE", instr.result))
            case "cjump":
                self._push_value(instr.arg1)
                tl, fl = instr.arg2
                self.instructions.append(Instruction("JIF", tl))
                self.instructions.append(Instruction("JMP", fl))
            case "jump":
                self.instructions.append(Instruction("JMP", instr.arg1))
            case "label":
                self.instructions.append(LabelInstr(instr.result))
            case "print":
                self._push_value(instr.arg1)
                self.instructions.append(Instruction("PRINT"))

    def _push_value(self, val):
        if isinstance(val, str) and not val.startswith('"'):
            self.instructions.append(Instruction("LOAD", val))
        else:
            self.instructions.append(Instruction("PUSH", val))

    def print_code(self):
        print("\n===== Target Assembly =====")
        for instr in self.instructions: print(instr)
        print("===========================\n")
