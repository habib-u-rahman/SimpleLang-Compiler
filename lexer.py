# lexer.py — Token type constants for SimpleLang


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
