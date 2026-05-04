#!/usr/bin/env python3
# main.py — SimpleLang Compiler Driver

import sys, os
from lexer        import Lexer,            LexerError
from parser       import Parser,           ParseError
from semantic     import SemanticAnalyser, SemanticError
from intermediate import TACGenerator
from optimizer    import Optimizer
from codegen      import CodeGenerator,    VirtualMachine


EXAMPLE_SOURCE = """\
int a = 10;
int b = 3;
int sum = a + b;
int product = a * b;
bool big = a > 5;
print(sum);
print(product);
if (big) {
    print(a);
} else {
    print(b);
}
int counter = 0;
while (counter < 3) {
    print(counter);
    counter = counter + 1;
}
"""


def compile_and_run(source: str, dump: bool = False) -> bool:
    print("\n[1/6] Lexical analysis ...")
    try:
        tokens = Lexer(source).tokenize()
    except LexerError as e:
        print(f"  Lexer error: {e}"); return False
    if dump:
        for tok in tokens: print(f"    {tok}")

    print("[2/6] Parsing ...")
    try:
        ast = Parser(tokens).parse()
    except ParseError as e:
        print(f"  Parse error: {e}"); return False
    if dump:
        import pprint; pprint.pprint(ast, indent=4)

    print("[3/6] Semantic analysis ...")
    try:
        sym = SemanticAnalyser().analyse(ast)
    except SemanticError as e:
        print(e); return False
    if dump: sym.display()

    print("[4/6] Generating three-address code ...")
    gen = TACGenerator(); tac = gen.generate(ast)
    if dump: gen.print_code()

    print("[5/6] Optimising ...")
    opt_tac = Optimizer().optimize(tac)
    if dump: Optimizer.print_code(opt_tac, title="Optimised TAC")

    print("[6/6] Generating target code ...")
    cg = CodeGenerator(); asm = cg.generate(opt_tac)
    if dump: cg.print_code()

    print("\n===== Program Output =====")
    VirtualMachine(asm).run()
    print("==========================\n")
    return True


def main():
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print("SimpleLang Compiler\n")
        print("Usage:")
        print("  python main.py <source.sl>          # compile and run")
        print("  python main.py <source.sl> --dump   # show every phase")
        print("  python main.py --example            # run built-in demo")
        return
    if args[0] == "--example":
        print("=== Running built-in example ===")
        compile_and_run(EXAMPLE_SOURCE, dump="--dump" in args)
        return
    src_file = args[0]
    dump = "--dump" in args
    if not os.path.isfile(src_file):
        print(f"Error: file not found: {src_file!r}"); sys.exit(1)
    with open(src_file, "r", encoding="utf-8") as f:
        source = f.read()
    success = compile_and_run(source, dump=dump)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
