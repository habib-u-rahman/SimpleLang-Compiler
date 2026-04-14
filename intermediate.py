# =============================================================
# intermediate.py — Three-Address Code (TAC) Generator
#
# Translates the type-checked AST into a linear sequence of
# Three-Address Code instructions:
#
#   t0 = a + b            (BinOp)
#   t1 = -t0              (UnaryOp)
#   x  = t1               (Copy)
#   if t2 goto L1         (CondJump)
#   goto L2               (Jump)
#   L1:                   (Label)
#   param t3              (Param  – used by print)
#   print t3              (Print)
# =============================================================

from __future__ import annotations
from dataclasses import dataclass, field
from parser import (
    ProgramNode, DeclNode, AssignNode, IfNode, WhileNode,
    PrintNode, BlockNode, BinOpNode, UnaryOpNode, LiteralNode, IdentNode,
)


# ------------------------------------------------------------------
# TAC instruction dataclass
# ------------------------------------------------------------------

@dataclass
class TACInstr:
    op: str                    # 'assign' | 'binop' | 'unary' | 'jump'
                               # 'cjump' | 'label' | 'print'
    result: str | None = None  # destination temp / variable
    arg1: object = None        # first operand
    arg2: object = None        # second operand (binary ops)

    def __str__(self):
        match self.op:
            case "assign": return f"    {self.result} = {self.arg1}"
            case "binop":  return f"    {self.result} = {self.arg1} {self.arg2} "  \
                                  f"{self.result}"   # placeholder – see _gen_binop
            case "label":  return f"{self.result}:"
            case "jump":   return f"    goto {self.arg1}"
            case "cjump":  return f"    if {self.arg1} goto {self.arg2}"
            case "print":  return f"    print {self.arg1}"
            case _:        return f"    [{self.op}] {self.result} {self.arg1} {self.arg2}"


# We override __str__ properly below by storing everything we need.

@dataclass
class TAC:
    """A single Three-Address Code instruction with flexible printing."""
    op: str
    result: str | None = None
    arg1: object = None
    arg2: object = None

    def __str__(self):
        match self.op:
            case "assign":
                return f"    {self.result} = {self.arg1}"
            case "binop":
                return f"    {self.result} = {self.arg1} {self.arg2[0]} {self.arg2[1]}"
            case "unary":
                return f"    {self.result} = {self.arg1}{self.arg2}"
            case "label":
                return f"{self.result}:"
            case "jump":
                return f"    goto {self.arg1}"
            case "cjump":
                # arg1 = condition temp, arg2 = (true_label, false_label)
                tl, fl = self.arg2
                return f"    if {self.arg1} goto {tl} else goto {fl}"
            case "print":
                return f"    print {self.arg1}"
            case _:
                return f"    {self.op} {self.result} {self.arg1} {self.arg2}"


# ------------------------------------------------------------------
# TAC Generator
# ------------------------------------------------------------------

OP_SYMBOL = {
    "PLUS": "+", "MINUS": "-", "STAR": "*", "SLASH": "/", "PERCENT": "%",
    "EQ": "==", "NEQ": "!=", "LT": "<", "GT": ">", "LTE": "<=", "GTE": ">=",
    "AND": "&&", "OR": "||",
}


class TACGenerator:
    """
    Single-pass AST walker that emits TAC instructions into self.code.
    """

    def __init__(self):
        self.code: list[TAC] = []
        self._temp_count = 0
        self._label_count = 0

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _new_temp(self) -> str:
        t = f"t{self._temp_count}"
        self._temp_count += 1
        return t

    def _new_label(self) -> str:
        lbl = f"L{self._label_count}"
        self._label_count += 1
        return lbl

    def _emit(self, instr: TAC):
        self.code.append(instr)

    # ------------------------------------------------------------------
    # Entry point
    # ------------------------------------------------------------------

    def generate(self, tree: ProgramNode) -> list[TAC]:
        self._gen_program(tree)
        return self.code

    # ------------------------------------------------------------------
    # Statement generators
    # ------------------------------------------------------------------

    def _gen_program(self, node: ProgramNode):
        for stmt in node.stmts:
            self._gen_stmt(stmt)

    def _gen_stmt(self, node):
        match type(node).__name__:
            case "DeclNode":   self._gen_decl(node)
            case "AssignNode": self._gen_assign(node)
            case "IfNode":     self._gen_if(node)
            case "WhileNode":  self._gen_while(node)
            case "PrintNode":  self._gen_print(node)
            case "BlockNode":  self._gen_block(node)

    def _gen_decl(self, node: DeclNode):
        if node.init is not None:
            src = self._gen_expr(node.init)
            self._emit(TAC("assign", result=node.name, arg1=src))
        else:
            # Initialise to zero-equivalent
            default = {"int": 0, "float": 0.0, "bool": False, "string": ""
                       }.get(node.var_type, 0)
            self._emit(TAC("assign", result=node.name, arg1=default))

    def _gen_assign(self, node: AssignNode):
        src = self._gen_expr(node.expr)
        self._emit(TAC("assign", result=node.name, arg1=src))

    def _gen_if(self, node: IfNode):
        cond = self._gen_expr(node.condition)
        true_lbl  = self._new_label()
        false_lbl = self._new_label()
        end_lbl   = self._new_label()

        self._emit(TAC("cjump", arg1=cond, arg2=(true_lbl, false_lbl)))
        self._emit(TAC("label", result=true_lbl))
        self._gen_stmt(node.then_block)
        self._emit(TAC("jump", arg1=end_lbl))
        self._emit(TAC("label", result=false_lbl))
        if node.else_block:
            self._gen_stmt(node.else_block)
        self._emit(TAC("label", result=end_lbl))

    def _gen_while(self, node: WhileNode):
        start_lbl = self._new_label()
        body_lbl  = self._new_label()
        end_lbl   = self._new_label()

        self._emit(TAC("label", result=start_lbl))
        cond = self._gen_expr(node.condition)
        self._emit(TAC("cjump", arg1=cond, arg2=(body_lbl, end_lbl)))
        self._emit(TAC("label", result=body_lbl))
        self._gen_stmt(node.body)
        self._emit(TAC("jump", arg1=start_lbl))
        self._emit(TAC("label", result=end_lbl))

    def _gen_print(self, node: PrintNode):
        src = self._gen_expr(node.expr)
        self._emit(TAC("print", arg1=src))

    def _gen_block(self, node: BlockNode):
        for stmt in node.stmts:
            self._gen_stmt(stmt)

    # ------------------------------------------------------------------
    # Expression generators — return the name of the result temp/var
    # ------------------------------------------------------------------

    def _gen_expr(self, node) -> str | object:
        match type(node).__name__:
            case "LiteralNode": return self._gen_literal(node)
            case "IdentNode":   return node.name
            case "BinOpNode":   return self._gen_binop(node)
            case "UnaryOpNode": return self._gen_unary(node)
            case _:             return "??"

    def _gen_literal(self, node: LiteralNode):
        # Inline small literals; wrap strings in quotes for readability
        if node.lit_type == "string":
            return f'"{node.value}"'
        return node.value

    def _gen_binop(self, node: BinOpNode):
        l = self._gen_expr(node.left)
        r = self._gen_expr(node.right)
        t = self._new_temp()
        sym = OP_SYMBOL.get(node.op, node.op)
        self._emit(TAC("binop", result=t, arg1=l, arg2=(sym, r)))
        return t

    def _gen_unary(self, node: UnaryOpNode):
        operand = self._gen_expr(node.operand)
        t = self._new_temp()
        sym = "!" if node.op == "NOT" else "-"
        self._emit(TAC("unary", result=t, arg1=sym, arg2=operand))
        return t

    # ------------------------------------------------------------------
    # Display
    # ------------------------------------------------------------------

    def print_code(self):
        print("\n===== Three-Address Code =====")
        for instr in self.code:
            print(instr)
        print("==============================\n")


# ------------------------------------------------------------------
# Quick standalone test
# ------------------------------------------------------------------
if __name__ == "__main__":
    from lexer import Lexer
    from parser import Parser
    from semantic import SemanticAnalyser

    src = """
    int x = 10;
    int y = x + 5;
    if (x > 5) {
        print(y);
    } else {
        print(x);
    }
    """
    tokens = Lexer(src).tokenize()
    ast    = Parser(tokens).parse()
    SemanticAnalyser().analyse(ast)
    gen = TACGenerator()
    gen.generate(ast)
    gen.print_code()
