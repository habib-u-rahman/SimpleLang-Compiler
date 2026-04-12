# parser.py — Recursive-Descent Parser for SimpleLang

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, List
from lexer import Lexer, Token, TT


@dataclass
class ProgramNode:
    stmts: List = field(default_factory=list)

@dataclass
class DeclNode:
    var_type: str
    name: str
    init: Optional[object] = None

@dataclass
class AssignNode:
    name: str
    expr: object = None

@dataclass
class IfNode:
    condition: object
    then_block: object
    else_block: Optional[object] = None

@dataclass
class WhileNode:
    condition: object
    body: object

@dataclass
class PrintNode:
    expr: object

@dataclass
class BlockNode:
    stmts: List = field(default_factory=list)

@dataclass
class BinOpNode:
    op: str
    left: object
    right: object

@dataclass
class UnaryOpNode:
    op: str
    operand: object

@dataclass
class LiteralNode:
    value: object
    lit_type: str

@dataclass
class IdentNode:
    name: str


class ParseError(Exception):
    pass


class Parser:
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.pos = 0

    def _peek(self) -> Token:
        return self.tokens[self.pos]

    def _advance(self) -> Token:
        tok = self.tokens[self.pos]
        if tok.type != TT.EOF:
            self.pos += 1
        return tok

    def _check(self, *types) -> bool:
        return self._peek().type in types

    def _match(self, *types) -> Optional[Token]:
        if self._check(*types):
            return self._advance()
        return None

    def _expect(self, ttype: str, msg: str = "") -> Token:
        tok = self._peek()
        if tok.type != ttype:
            raise ParseError(
                msg or f"Expected {ttype} but got {tok.type!r} "
                       f"at line {tok.line}, col {tok.col}"
            )
        return self._advance()

    def parse(self) -> ProgramNode:
        stmts = []
        while not self._check(TT.EOF):
            stmts.append(self._stmt())
        return ProgramNode(stmts)

    def _stmt(self):
        tok = self._peek()
        if tok.type in (TT.INT, TT.FLOAT_KW, TT.BOOL_KW, TT.STRING_KW):
            return self._decl_stmt()
        elif tok.type == TT.IDENT:
            return self._assign_stmt()
        elif tok.type == TT.IF:
            return self._if_stmt()
        elif tok.type == TT.WHILE:
            return self._while_stmt()
        elif tok.type == TT.PRINT:
            return self._print_stmt()
        elif tok.type == TT.LBRACE:
            return self._block()
        else:
            raise ParseError(f"Unexpected token {tok.type!r} at line {tok.line}, col {tok.col}")

    def _decl_stmt(self):
        type_map = {TT.INT: "int", TT.FLOAT_KW: "float", TT.BOOL_KW: "bool", TT.STRING_KW: "string"}
        var_type = type_map[self._advance().type]
        name = self._expect(TT.IDENT).value
        init = None
        if self._match(TT.ASSIGN):
            init = self._expr()
        self._expect(TT.SEMICOLON)
        return DeclNode(var_type, name, init)

    def _assign_stmt(self):
        name = self._expect(TT.IDENT).value
        self._expect(TT.ASSIGN)
        expr = self._expr()
        self._expect(TT.SEMICOLON)
        return AssignNode(name, expr)

    def _if_stmt(self):
        self._expect(TT.IF)
        self._expect(TT.LPAREN)
        cond = self._expr()
        self._expect(TT.RPAREN)
        then_blk = self._block()
        else_blk = None
        if self._match(TT.ELSE):
            else_blk = self._block()
        return IfNode(cond, then_blk, else_blk)

    def _while_stmt(self):
        self._expect(TT.WHILE)
        self._expect(TT.LPAREN)
        cond = self._expr()
        self._expect(TT.RPAREN)
        body = self._block()
        return WhileNode(cond, body)

    def _print_stmt(self):
        self._expect(TT.PRINT)
        self._expect(TT.LPAREN)
        expr = self._expr()
        self._expect(TT.RPAREN)
        self._expect(TT.SEMICOLON)
        return PrintNode(expr)

    def _block(self):
        self._expect(TT.LBRACE)
        stmts = []
        while not self._check(TT.RBRACE, TT.EOF):
            stmts.append(self._stmt())
        self._expect(TT.RBRACE)
        return BlockNode(stmts)

    def _expr(self):       return self._or_expr()

    def _or_expr(self):
        node = self._and_expr()
        while self._check(TT.OR):
            op = self._advance().type
            node = BinOpNode(op, node, self._and_expr())
        return node

    def _and_expr(self):
        node = self._eq_expr()
        while self._check(TT.AND):
            op = self._advance().type
            node = BinOpNode(op, node, self._eq_expr())
        return node

    def _eq_expr(self):
        node = self._rel_expr()
        while self._check(TT.EQ, TT.NEQ):
            op = self._advance().type
            node = BinOpNode(op, node, self._rel_expr())
        return node

    def _rel_expr(self):
        node = self._add_expr()
        while self._check(TT.LT, TT.GT, TT.LTE, TT.GTE):
            op = self._advance().type
            node = BinOpNode(op, node, self._add_expr())
        return node

    def _add_expr(self):
        node = self._mul_expr()
        while self._check(TT.PLUS, TT.MINUS):
            op = self._advance().type
            node = BinOpNode(op, node, self._mul_expr())
        return node

    def _mul_expr(self):
        node = self._unary()
        while self._check(TT.STAR, TT.SLASH, TT.PERCENT):
            op = self._advance().type
            node = BinOpNode(op, node, self._unary())
        return node

    def _unary(self):
        if self._check(TT.NOT, TT.MINUS):
            op = self._advance().type
            return UnaryOpNode(op, self._unary())
        return self._primary()

    def _primary(self):
        tok = self._peek()
        if tok.type == TT.INTEGER:
            self._advance(); return LiteralNode(tok.value, "int")
        if tok.type == TT.FLOAT:
            self._advance(); return LiteralNode(tok.value, "float")
        if tok.type == TT.STRING:
            self._advance(); return LiteralNode(tok.value, "string")
        if tok.type in (TT.TRUE, TT.FALSE):
            self._advance(); return LiteralNode(tok.value, "bool")
        if tok.type == TT.IDENT:
            self._advance(); return IdentNode(tok.value)
        if tok.type == TT.LPAREN:
            self._advance()
            node = self._expr()
            self._expect(TT.RPAREN)
            return node
        raise ParseError(f"Unexpected token {tok.type!r} at line {tok.line}, col {tok.col}")
