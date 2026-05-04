# lexer.py — Lexical Analyser (Tokeniser) for SimpleLang

import re
from dataclasses import dataclass
from typing import Optional


class TT:
    INTEGER = "INTEGER";  FLOAT = "FLOAT"
    STRING  = "STRING";   BOOL  = "BOOL"
    IDENT   = "IDENT"
    INT       = "INT";    FLOAT_KW  = "FLOAT_KW"
    BOOL_KW   = "BOOL_KW"; STRING_KW = "STRING_KW"
    IF = "IF"; ELSE = "ELSE"; WHILE = "WHILE"
    PRINT = "PRINT"; TRUE = "TRUE"; FALSE = "FALSE"
    PLUS = "PLUS"; MINUS = "MINUS"; STAR = "STAR"
    SLASH = "SLASH"; PERCENT = "PERCENT"
    EQ = "EQ"; NEQ = "NEQ"; LT = "LT"; GT = "GT"
    LTE = "LTE"; GTE = "GTE"
    AND = "AND"; OR = "OR"; NOT = "NOT"
    ASSIGN    = "ASSIGN"
    LPAREN    = "LPAREN";   RPAREN    = "RPAREN"
    LBRACE    = "LBRACE";   RBRACE    = "RBRACE"
    SEMICOLON = "SEMICOLON"; COMMA = "COMMA"; EOF = "EOF"


KEYWORDS = {
    "int":    TT.INT,      "float":  TT.FLOAT_KW,
    "bool":   TT.BOOL_KW,  "string": TT.STRING_KW,
    "if":     TT.IF,       "else":   TT.ELSE,
    "while":  TT.WHILE,    "print":  TT.PRINT,
    "true":   TT.TRUE,     "false":  TT.FALSE,
}


@dataclass
class Token:
    type: str
    value: object
    line: int
    col: int

    def __repr__(self):
        return f"Token({self.type}, {self.value!r}, line={self.line}, col={self.col})"


class LexerError(Exception):
    pass


class Lexer:
    TOKEN_SPEC = [
        ("FLOAT",     r"\d+\.\d+"),
        ("INTEGER",   r"\d+"),
        ("STRING",    r'"[^"]*"'),
        ("EQ",        r"=="),
        ("NEQ",       r"!="),
        ("LTE",       r"<="),
        ("GTE",       r">="),
        ("AND",       r"&&"),
        ("OR",        r"\|\|"),
        ("LT",        r"<"),
        ("GT",        r">"),
        ("ASSIGN",    r"="),
        ("PLUS",      r"\+"),
        ("MINUS",     r"-"),
        ("STAR",      r"\*"),
        ("SLASH",     r"/"),
        ("PERCENT",   r"%"),
        ("NOT",       r"!"),
        ("LPAREN",    r"\("),
        ("RPAREN",    r"\)"),
        ("LBRACE",    r"\{"),
        ("RBRACE",    r"\}"),
        ("SEMICOLON", r";"),
        ("COMMA",     r","),
        ("IDENT",     r"[a-zA-Z_]\w*"),
        ("NEWLINE",   r"\n"),
        ("SKIP",      r"[ \t\r]+"),
        ("COMMENT",   r"//[^\n]*"),
        ("MISMATCH",  r"."),
    ]

    master_re = re.compile(
        "|".join(f"(?P<{name}>{pattern})" for name, pattern in TOKEN_SPEC)
    )

    def __init__(self, source: str):
        self.source = source

    def tokenize(self) -> list[Token]:
        tokens: list[Token] = []
        line = 1
        line_start = 0

        for mo in self.master_re.finditer(self.source):
            kind  = mo.lastgroup
            value = mo.group()
            col   = mo.start() - line_start + 1

            if kind == "NEWLINE":
                line += 1
                line_start = mo.end()
            elif kind in ("SKIP", "COMMENT"):
                pass
            elif kind == "MISMATCH":
                raise LexerError(f"Unexpected character {value!r} at line {line}, col {col}")
            else:
                if kind == "IDENT" and value in KEYWORDS:
                    kind = KEYWORDS[value]
                if kind == "INTEGER":
                    value = int(value)
                elif kind == "FLOAT":
                    value = float(value)
                elif kind == "STRING":
                    value = value[1:-1]
                elif kind in (TT.TRUE, TT.FALSE):
                    value = (kind == TT.TRUE)
                tokens.append(Token(kind, value, line, col))

        tokens.append(Token(TT.EOF, None, line, 0))
        return tokens
