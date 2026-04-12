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
        raise NotImplementedError("Statement parsing coming soon")
