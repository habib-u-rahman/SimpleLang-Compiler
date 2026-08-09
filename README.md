<div align="center">

<img width="100%" src="https://capsule-render.vercel.app/api?type=waving&height=200&color=0:00D9FF,50:A855F7,100:FF0080&text=SimpleLang%20Compiler&fontSize=46&fontColor=FFFFFF&fontAlignY=34&desc=A%20complete%20compiler%20built%20from%20scratch%20in%20Python&descSize=16&descAlignY=54&animation=fadeIn" alt="banner" />

<img src="https://readme-typing-svg.demolab.com?font=Fira+Code&weight=600&size=19&duration=3000&pause=900&color=00D9FF&center=true&vCenter=true&width=620&height=45&lines=Source+%E2%86%92+Tokens+%E2%86%92+AST+%E2%86%92+IR+%E2%86%92+Optimised+Code;Every+stage+hand-written+%E2%80%94+no+parser+generators;Lexer+%C2%B7+Parser+%C2%B7+Semantics+%C2%B7+Codegen" alt="typing" />

<br/><br/>

<img src="https://img.shields.io/badge/Python-3.8+-3776AB?style=for-the-badge&logo=python&logoColor=white" />
<img src="https://img.shields.io/badge/Compiler_Design-A855F7?style=for-the-badge" />
<img src="https://img.shields.io/badge/GUI-Included-FF0080?style=for-the-badge" />
<br/>
<img src="https://img.shields.io/github/last-commit/habib-u-rahman/SimpleLang-Compiler?style=for-the-badge&color=00D9FF&labelColor=0D1117" />
<img src="https://img.shields.io/github/languages/top/habib-u-rahman/SimpleLang-Compiler?style=for-the-badge&color=A855F7&labelColor=0D1117" />

</div>

<div align="center">
  <img width="100%" src="https://raw.githubusercontent.com/Anmol-Baranwal/Cool-GIFs-For-GitHub/main/Assets/Line.gif" alt="divider" />
</div>

## 🎯 &nbsp;What This Is

**SimpleLang** is a small programming language, and this repository is its
compiler — written entirely from scratch in Python, with **no parser generators,
no ANTLR, no PLY**. Every stage of the classic compiler pipeline is implemented
by hand.

It compiles `.sl` source files, supports variables, arithmetic, conditionals and
loops, and reports errors with useful messages instead of a stack trace.

> 📚 &nbsp;Built to understand how compilers actually work — the kind of thing you
> only really learn by writing every stage yourself.

<div align="center">
  <img width="100%" src="https://raw.githubusercontent.com/Anmol-Baranwal/Cool-GIFs-For-GitHub/main/Assets/Line.gif" alt="divider" />
</div>

## 🔬 &nbsp;The Pipeline

```mermaid
flowchart LR
    A["📄 program.sl<br/>source"] --> B["🔤 Lexer<br/>lexer.py"]
    B --> C["🌳 Parser<br/>parser.py"]
    C --> D["✅ Semantic Analysis<br/>semantic.py"]
    D <--> E["📋 Symbol Table<br/>symbol_table.py"]
    D --> F["⚙️ Intermediate Code<br/>intermediate.py"]
    F --> G["✨ Optimizer<br/>optimizer.py"]
    G --> H["🎯 Code Generation<br/>codegen.py"]
    H --> I["💾 Output"]

    style A fill:#0D1117,stroke:#00D9FF,color:#C9D1D9
    style B fill:#0D1117,stroke:#00D9FF,color:#C9D1D9
    style C fill:#0D1117,stroke:#A855F7,color:#C9D1D9
    style D fill:#0D1117,stroke:#A855F7,color:#C9D1D9
    style E fill:#0D1117,stroke:#A855F7,color:#C9D1D9
    style F fill:#0D1117,stroke:#FF0080,color:#C9D1D9
    style G fill:#0D1117,stroke:#FF0080,color:#C9D1D9
    style H fill:#0D1117,stroke:#FF0080,color:#C9D1D9
    style I fill:#0D1117,stroke:#00D9FF,color:#C9D1D9
```

| Stage | File | What it does |
|:------|:-----|:-------------|
| **Lexical Analysis** | `lexer.py` | Turns raw source text into a token stream |
| **Parsing** | `parser.py` | Builds an abstract syntax tree from the tokens |
| **Semantic Analysis** | `semantic.py` | Type checking, scope rules, undeclared-variable detection |
| **Symbol Table** | `symbol_table.py` | Tracks identifiers, types and scope across the program |
| **Intermediate Code** | `intermediate.py` | Emits a target-independent IR |
| **Optimization** | `optimizer.py` | Simplifies the IR before generation |
| **Code Generation** | `codegen.py` | Produces the final output code |

<div align="center">
  <img width="100%" src="https://raw.githubusercontent.com/Anmol-Baranwal/Cool-GIFs-For-GitHub/main/Assets/Line.gif" alt="divider" />
</div>

## ✨ &nbsp;Features

<table>
<tr>
<td width="50%" valign="top">

### 🧩 &nbsp;Language Support
- Variables and assignment
- Arithmetic expressions with precedence
- Conditional statements (`if` / `else`)
- Loop constructs
- Error reporting with line context

</td>
<td width="50%" valign="top">

### 🛠️ &nbsp;Compiler Features
- Hand-written lexer and parser
- Symbol table with scope tracking
- Intermediate representation
- Optimization pass
- **GUI front end** (`gui.py`)

</td>
</tr>
</table>

<div align="center">
  <img width="100%" src="https://raw.githubusercontent.com/Anmol-Baranwal/Cool-GIFs-For-GitHub/main/Assets/Line.gif" alt="divider" />
</div>

## ⚡ &nbsp;Quickstart

```bash
# Clone
git clone https://github.com/habib-u-rahman/SimpleLang-Compiler.git
cd SimpleLang-Compiler

# Compile a program from the CLI
python main.py program.sl

# Or launch the GUI
python gui.py
```

> ℹ️ &nbsp;Requires **Python 3.8+**. No external dependencies for the core compiler.

<div align="center">
  <img width="100%" src="https://raw.githubusercontent.com/Anmol-Baranwal/Cool-GIFs-For-GitHub/main/Assets/Line.gif" alt="divider" />
</div>

## 🧪 &nbsp;Test Programs

The repo ships with sample `.sl` programs that exercise each language feature:

| File | Exercises |
|:-----|:----------|
| `program.sl` | General-purpose sample program |
| `test_math.sl` | Arithmetic and operator precedence |
| `test_if.sl` | Conditional branching |
| `test_loop.sl` | Loop constructs |
| `test_error.sl` | Error detection and reporting |

```bash
python main.py test_math.sl
python main.py test_if.sl
python main.py test_loop.sl
python main.py test_error.sl    # should report errors, not crash
```

<div align="center">
  <img width="100%" src="https://raw.githubusercontent.com/Anmol-Baranwal/Cool-GIFs-For-GitHub/main/Assets/Line.gif" alt="divider" />
</div>

## 📁 &nbsp;Project Structure

```
SimpleLang-Compiler/
├── lexer.py            # tokenizer
├── parser.py           # AST builder
├── semantic.py         # type & scope checking
├── symbol_table.py     # identifier tracking
├── intermediate.py     # IR generation
├── optimizer.py        # IR optimization
├── codegen.py          # final code emission
├── main.py             # CLI entry point
├── gui.py              # graphical interface
└── *.sl                # sample programs
```

<div align="center">
  <img width="100%" src="https://raw.githubusercontent.com/Anmol-Baranwal/Cool-GIFs-For-GitHub/main/Assets/Line.gif" alt="divider" />
</div>

## 🗺️ &nbsp;Roadmap

- [x] Lexical analysis
- [x] Parsing and AST construction
- [x] Semantic analysis with symbol table
- [x] Intermediate code generation
- [x] Optimization pass
- [x] Code generation
- [x] GUI front end
- [ ] Function definitions and calls
- [ ] More optimization passes (constant folding, dead code elimination)
- [ ] Formal language grammar documentation

<div align="center">

<br/>

<a href="https://github.com/habib-u-rahman">
  <img src="https://img.shields.io/badge/Built_by_Habib--ur--rahman-0D1117?style=for-the-badge&logo=github&logoColor=00D9FF" height="38" />
</a>

<br/><br/>

<sub>⭐ <em>If this helped you understand compilers, a star means a lot.</em></sub>

<img width="100%" src="https://capsule-render.vercel.app/api?type=waving&height=120&section=footer&color=0:FF0080,50:A855F7,100:00D9FF&animation=fadeIn" alt="footer" />

</div>
