# intermediate.py — Three-Address Code Generator

from __future__ import annotations
from dataclasses import dataclass
from parser import (ProgramNode, DeclNode, AssignNode, IfNode, WhileNode,
                    PrintNode, BlockNode, BinOpNode, UnaryOpNode, LiteralNode, IdentNode)

OP_SYMBOL = {
    "PLUS": "+", "MINUS": "-", "STAR": "*", "SLASH": "/", "PERCENT": "%",
    "EQ": "==", "NEQ": "!=", "LT": "<", "GT": ">", "LTE": "<=", "GTE": ">=",
    "AND": "&&", "OR": "||",
}


@dataclass
class TAC:
    op: str
    result: str | None = None
    arg1: object = None
    arg2: object = None

    def __str__(self):
        match self.op:
            case "assign": return f"    {self.result} = {self.arg1}"
            case "binop":  return f"    {self.result} = {self.arg1} {self.arg2[0]} {self.arg2[1]}"
            case "unary":  return f"    {self.result} = {self.arg1}{self.arg2}"
            case "label":  return f"{self.result}:"
            case "jump":   return f"    goto {self.arg1}"
            case "cjump":
                tl, fl = self.arg2
                return f"    if {self.arg1} goto {tl} else goto {fl}"
            case "print":  return f"    print {self.arg1}"
            case _:        return f"    {self.op} {self.result} {self.arg1} {self.arg2}"


class TACGenerator:
    def __init__(self):
        self.code: list[TAC] = []
        self._temp_count = 0
        self._label_count = 0

    def _new_temp(self) -> str:
        t = f"t{self._temp_count}"; self._temp_count += 1; return t

    def _new_label(self) -> str:
        lbl = f"L{self._label_count}"; self._label_count += 1; return lbl

    def _emit(self, instr: TAC):
        self.code.append(instr)

    def generate(self, tree) -> list[TAC]:
        for stmt in tree.stmts:
            self._gen_stmt(stmt)
        return self.code

    def _gen_stmt(self, node):
        match type(node).__name__:
            case "DeclNode":   self._gen_decl(node)
            case "AssignNode": self._gen_assign(node)
            case "PrintNode":  self._gen_print(node)
            case "BlockNode":  self._gen_block(node)
            case "IfNode":     self._gen_if(node)
            case "WhileNode":  self._gen_while(node)

    def _gen_decl(self, node):
        src = self._gen_expr(node.init) if node.init is not None else 0
        self._emit(TAC("assign", result=node.name, arg1=src))

    def _gen_assign(self, node):
        src = self._gen_expr(node.expr)
        self._emit(TAC("assign", result=node.name, arg1=src))

    def _gen_print(self, node):
        src = self._gen_expr(node.expr)
        self._emit(TAC("print", arg1=src))

    def _gen_block(self, node):
        for stmt in node.stmts:
            self._gen_stmt(stmt)

    def _gen_if(self, node):
        cond = self._gen_expr(node.condition)
        true_lbl = self._new_label(); false_lbl = self._new_label(); end_lbl = self._new_label()
        self._emit(TAC("cjump", arg1=cond, arg2=(true_lbl, false_lbl)))
        self._emit(TAC("label", result=true_lbl))
        self._gen_stmt(node.then_block)
        self._emit(TAC("jump", arg1=end_lbl))
        self._emit(TAC("label", result=false_lbl))
        if node.else_block:
            self._gen_stmt(node.else_block)
        self._emit(TAC("label", result=end_lbl))

    def _gen_while(self, node):
        # basic while — labels will be fixed in next commit
        start_lbl = self._new_label(); end_lbl = self._new_label()
        self._emit(TAC("label", result=start_lbl))
        cond = self._gen_expr(node.condition)
        self._emit(TAC("cjump", arg1=cond, arg2=(start_lbl, end_lbl)))
        self._gen_stmt(node.body)
        self._emit(TAC("jump", arg1=start_lbl))
        self._emit(TAC("label", result=end_lbl))

    def _gen_expr(self, node):
        match type(node).__name__:
            case "LiteralNode":
                return f'"{node.value}"' if node.lit_type == "string" else node.value
            case "IdentNode": return node.name
            case "BinOpNode": return self._gen_binop(node)
            case "UnaryOpNode": return self._gen_unary(node)
            case _: return "??"

    def _gen_binop(self, node):
        l = self._gen_expr(node.left); r = self._gen_expr(node.right)
        t = self._new_temp(); sym = OP_SYMBOL.get(node.op, node.op)
        self._emit(TAC("binop", result=t, arg1=l, arg2=(sym, r)))
        return t

    def _gen_unary(self, node):
        operand = self._gen_expr(node.operand); t = self._new_temp()
        sym = "!" if node.op == "NOT" else "-"
        self._emit(TAC("unary", result=t, arg1=sym, arg2=operand))
        return t

    def print_code(self):
        print("\n===== Three-Address Code =====")
        for instr in self.code: print(instr)
        print("==============================\n")
