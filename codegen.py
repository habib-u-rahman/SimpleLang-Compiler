# codegen.py — Target Code Generator skeleton for SimpleLang

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
        # full instruction translation coming in next commit
        self.instructions.append(Instruction("HALT"))
        return self.instructions
