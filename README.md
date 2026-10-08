# Tomasulo Algorithm Simulator with Multi-Issue Support

A Python simulator of the Tomasulo algorithm with a reorder buffer (ROB), register
renaming (RAT), reservation stations, a load/store queue with store-to-load
forwarding, and one common data bus (CDB).

This version adds **in-order multi-issue: 1 to 4 instructions per cycle**, set by
`Issue width = N` in the input file (default 1).

## Requirements
Python 3. No extra packages.

## How to run
```
cd code
python3 main.py
```
This runs `test_case.txt` (the file name is set at the top of `main.py`).
To run another input file:
```
python3 main.py tests/test1_loop_w2.txt
```
To save the output to a file:
```
python3 main.py > output_w1.txt
```

## Input file format
```
               # of rs   Cycles in EX   Cycles in Mem   # of FUs
Integer adder   4         1                              1
FP adder        3         4                              1
FP multiplier   2         15                             1
Load/store unit 5         1              5               1

ROB entries = 64
Issue width = 2
R1=12, R2=32, F20=3.0
Mem[4]=3.0, Mem[8]=2.0

Ld F2 0(R1)
Mult.d F4 F2 F20
...
```
- `Issue width` can be 1 to 4. If the line is missing, the width is 1.
- Instructions are case insensitive, and commas are optional (`add.d f1, f2, f3` works).
- Supported instructions: `Ld`, `Sd`, `Add`, `Addi`, `Sub`, `Add.d`, `Sub.d`, `Mult.d`, `Bne`, `Beq`.

## Output
1. The instruction status table with the cycle(s) of ISSUE, EXE, MEM, WB and COMMIT.
2. Total cycles.
3. The final values of all integer and FP registers.
4. All non-zero memory values.

## Tests
```
cd code
python3 run_tests.py
```
This runs every input file in `tests/` (4 programs, each at widths 1, 2, 3 and 4),
saves each output to its own file in `results/`, and checks the final registers and
memory against `reference_check.py`, which runs the program one instruction at a
time with no pipeline. Every line should end in `CORRECT`.

| Test | What it checks |
|---|---|
| `test1_loop` | the given test case: loads, FP operations, a store, and a loop with `Bne` |
| `test2_dependencies` | dependencies between instructions issued in the same cycle, renaming the same register twice, writing to R0 |
| `test3_memory_branches` | store-to-load forwarding, `Beq` taken and not taken, small reservation stations, lower-case input with commas |
| `test4_small_rob` | a 4-entry ROB, so issue has to stall when it is full |

## Folder layout
```
tomasulo-python/
├── README.md             this file
├── data_structure.txt    fields of each data structure (ROB, RS, RAT, ...)
├── report.md / report.pdf / report.tex / references.bib
└── code/
    ├── main.py, init.py, issue.py, exe.py, mem.py, wb.py, commit.py, print_status.py
    ├── reference_check.py, run_tests.py
    ├── test_case.txt, code.in
    ├── tests/            16 test input files
    └── results/          16 test outputs, one file per run
```

## Files (all inside `code/`)
| File | What it does |
|---|---|
| `main.py` | reads the input file, runs the five stages every cycle, prints the results |
| `init.py` | data structures and `parse_input()` for the input file |
| `issue.py` | issues up to N instructions per cycle, in program order |
| `exe.py` | execution units and branch resolution |
| `mem.py` | load/store memory stage and store-to-load forwarding |
| `wb.py` | one CDB broadcast per cycle |
| `commit.py` | commits up to N instructions per cycle, in order |
| `print_status.py` | debug printing helpers |
| `reference_check.py` | reference interpreter used by the tests |
| `run_tests.py` | runs all tests and saves the outputs |
| `tests/` | test input files |
| `results/` | test outputs, one file per run |

## Limitations
- No branch prediction: fetch stops at a branch until it is resolved in EX.
- One CDB, so at most one result is broadcast per cycle.

See `report.pdf` (or `report.md`) for details.