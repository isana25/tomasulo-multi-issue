# Tomasulo Algorithm Simulator with Multi-Issue Support

A Python simulator of the Tomasulo algorithm with a reorder buffer (ROB), register
renaming (RAT), reservation stations, a load/store queue with store-to-load
forwarding, and one common data bus (CDB).

This version adds **in-order multi-issue: 1 to 4 instructions per cycle**, set by
`Issue width = N` in the input file (default 1).

## Assignment Requirements
The goal is to add in-order multi-issue support (issue width 1 to 4) to an existing Tomasulo simulator. The table maps each requirement to its implementation.

| # | Requirement | Where it is implemented | Status |
|---|---|---|---|
| 1 | In-order multi-issue, 1 to 4 instructions per cycle | `code/issue.py`: `issue()` loop over `issue_one()`; `code/commit.py`: `commit()` commits up to N per cycle | Done |
| 2 | Issue width set in the input file with `Issue width = N` (default 1) | `code/init.py`: `parse_input()`; passed to issue and commit in `code/main.py` | Done |
| 3 | Output: instruction status table, final register values, non-zero memory values | `code/commit.py`: `print_ROB()` prints each row; `code/main.py` prints total cycles, registers and memory | Done |
| 4 | Test cases for different issue widths, with results reported | `code/tests/` (20 inputs), `code/results/` (20 outputs), `code/run_tests.py`, `code/reference_check.py`; results in the report | Done |
| 5 | Submit code, test cases, README and report to GitHub | This repository | Done |

## Implementation Overview
- **Multi-issue:** the issue stage issues up to N instructions per cycle (N = 1 to 4), in program order. It stops early when the ROB, a reservation station or the load/store queue is full, or after a branch. Each instruction is renamed before the next one, so dependencies inside the same cycle are handled correctly.
- **Multi-commit:** up to N instructions commit per cycle from the head of the ROB, in program order.
- **Input file:** all settings (hardware table, ROB size, issue width, initial registers and memory, instructions) are read from one input file.
- **Output:** the instruction status table, total cycles, final register values and non-zero memory values.
- **Bug fixes in the provided code (10):** a unit could start two instructions in one cycle; a pipelined FP unit was advanced twice per cycle; a CDB broadcast could overwrite a newer register rename in the RAT; the simulation could stop before the last store finished writing memory; a load/store address calculation with more than 1 EX cycle never finished; the integer adder and address adder behaved as pipelined although they are unpipelined (the oldest ready instruction now also goes first); stores could write memory before reaching the ROB head; and three store-to-load forwarding bugs in `mem.py`.
- **Added:** `Beq` support, 20 test inputs (5 programs × widths 1–4), saved outputs for every run, and an automatic checker for final values and timing rules.

## Evaluation Results
All **20 of 20** test runs end with the correct final registers and memory (checked against a reference interpreter) and pass all timing checks. With width 1, the output for the provided test case is identical to the original simulator.

Total cycles:

| Test | Width 1 | Width 2 | Width 3 | Width 4 |
|---|---|---|---|---|
| test1_loop | 38 | 35 | 36 | 36 |
| test2_dependencies | 35 | 31 | 29 | 29 |
| test3_memory_branches | 41 | 37 | 40 | 40 |
| test4_small_rob | 23 | 21 | 21 | 21 |
| test5_latencies | 47 | 42 | 41 | 41 |

Going from width 1 to width 2 saves 2 to 5 cycles in every test. Wider issue saves at most 2 more cycles, because the single CDB, one unit of each type and the stall at every branch become the bottleneck. Full timing tables are in `code/results/`, and the full discussion is in the report.

## How to Run
The simulator is written in Python, so there is nothing to compile. It needs **Python 3** and no extra packages. It was run on macOS; it also works on Linux and Windows.

**Step 1: get the code.**
```
git clone https://github.com/isana25/tomasulo-multi-issue.git
```

**Step 2: open a terminal in the `code` folder.**
```
cd tomasulo-multi-issue/code
```

**Step 3: check Python.**
```
python3 --version
```
On Windows, use `python` instead of `python3` in all commands.

**Step 4: run the provided test case.**
```
python3 main.py
```
This runs `test_case.txt` and prints the timing table, the total cycles, the register values and the non-zero memory values.

**Step 5: run any other input file.**
```
python3 main.py tests/test1_loop_w2.txt
```
To change the issue width, edit the line `Issue width = N` (1 to 4) in the input file. If the line is missing, the width is 1.

**Step 6: save the output to a file.**
```
python3 main.py tests/test1_loop_w2.txt > output_w2.txt
```

**Step 7: run all the tests.**
```
python3 run_tests.py
```
This runs all 20 test inputs, prints one line per run (total cycles, final state and timing check), and saves each full output to `results/<test>_w<width>.out`. The last line is `ALL TESTS PASSED` when every check passes.

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
`run_tests.py` runs every input file in `tests/` (5 programs, each at widths 1, 2, 3 and 4) and checks each run automatically:
- the final registers and memory must match `reference_check.py`, a simple interpreter that runs the program one instruction at a time with no pipeline;
- the timing table must follow the machine's rules: in-order issue, at most N issues and commits per cycle, one CDB broadcast per cycle, correct EX and MEM lengths, unpipelined units used by one instruction at a time, and stores writing memory only after older instructions commit.

| Test | What it checks |
|---|---|
| `test1_loop` | the provided test case: loads, FP operations, a store, and a loop with `Bne` |
| `test2_dependencies` | dependencies between instructions issued in the same cycle, renaming the same register twice, writing to R0 |
| `test3_memory_branches` | store-to-load forwarding, `Beq` taken and not taken, small reservation stations, lower-case input with commas |
| `test4_small_rob` | a 4-entry ROB, so issue has to stall when it is full |
| `test5_latencies` | 2 EX cycles for the integer adder and load/store unit, 3 MEM cycles, a loop and forwarding (unpipelined units) |

## Folder layout
```
tomasulo-multi-issue/
├── README.md             this file
├── data_structure.txt    fields of each data structure (ROB, RS, RAT, ...)
├── report.md / report.pdf / report.tex
└── code/
    ├── main.py, init.py, issue.py, exe.py, mem.py, wb.py, commit.py, print_status.py
    ├── reference_check.py, run_tests.py
    ├── test_case.txt, code.in
    ├── tests/            20 test input files
    └── results/          20 test outputs, one file per run
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
| `run_tests.py` | runs all tests, checks values and timing, and saves the outputs |
| `tests/` | test input files |
| `results/` | test outputs, one file per run |

## Limitations
- No branch prediction: fetching stops at every branch until it is resolved in EX.
- One CDB, so at most one result is broadcast per cycle.
- One functional unit of each type (a different number in the input file gives a warning).
- Branch offsets are in bytes, as in the provided code: `Bne R1 R0 -12` jumps back 3 instructions.