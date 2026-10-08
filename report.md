# Assignment 1 : Tomasulo Algorithm with Multi-Issue Support

**Name:** Sana Ashfaq   
**Course:** COSC6385 – Computer Architecture

## 1. Goal of the assignment

The Tomasulo algorithm lets a processor execute instructions out of order while still producing correct results. It renames registers with a register aliasing table (RAT), holds waiting instructions in reservation stations, broadcasts results on a common data bus (CDB), and uses a reorder buffer (ROB) to commit instructions in program order [1, 2].

The starting point is a working Python simulator of this algorithm that **issues only one instruction per cycle**. The goals of this assignment were to:

1. Add **in-order multi-issue**, so the simulator can issue **1 to 4 instructions per cycle**.
2. Let the user set the width in the input file with `Issue width = N` (the default is 1).
3. Print the instruction status table, the final register values and the non-zero memory values.
4. Write test cases that check the implementation at different issue widths, and report the results.

## 2. Summary of the work

The work consists of the following:

- An input-file parser, so that all settings, including the issue width, are read from one input file.
- A modified **issue** stage that issues up to N instructions per cycle, in program order.
- A modified **commit** stage that commits up to N instructions per cycle, in program order.
- Fixes for four bugs in the provided code that appear (or become worse) with multi-issue.
- Support for `Beq`, which is part of the instruction set but was missing from the provided code.
- A test suite of 4 programs, each run at widths 1, 2, 3 and 4 (16 runs). Every output is saved to its own file and checked automatically against a reference interpreter.

With issue width 1, the modified simulator produces **exactly the same timing table** as the original code on the provided test case. All **16 of 16** test runs end with the correct registers and memory.

## 3. Implementation

### Reading the input file (`init.py`, `main.py`)
- A new function `parse_input()` reads the hardware table (number of reservation stations, EX cycles and MEM cycles), `ROB entries = N`, **`Issue width = N`**, the initial registers and memory, and the instructions. In the provided code all of these values were hardcoded in `main.py`.
- The issue width is limited to 1–4. If the line is missing, the width is 1.
- The input is case insensitive and commas are optional, as the assignment says.
- At the end of the run, `main.py` now prints the total cycles, all register values and the non-zero memory values.

### Issue stage (`issue.py`)
- The original issue code was renamed to `issue_one()`. It now returns `True` if the instruction was issued and `False` if it stalled because the ROB, the reservation station or the load/store queue was full.
- A new `issue()` function calls `issue_one()` up to `issue_width` times per cycle. It stops early at the end of the program, at a structural stall (issue is in order, so no instruction behind a stalled one may issue), or after a branch.
- **Dependencies inside one issue group:** each instruction is renamed and the RAT is updated before the next one is decoded. So if instruction 2 reads a register that instruction 1 writes in the same cycle, it gets instruction 1's ROB tag instead of the old value.
- **Branches:** the provided code has no branch predictor. It stops fetching after a branch until the branch is resolved in EX. This rule is preserved: a branch is the last instruction of its issue group, and fetching restarts in the cycle after it resolves. Because nothing is fetched past an unresolved branch, there is never wrong-path work to squash.
- `Beq` was added (the provided code only had `Bne`), and the `offset(Rx)` operand of `Ld`/`Sd` now also works with two-digit registers such as `0(R12)`.

### Commit stage (`commit.py`)
- Up to `issue_width` instructions commit per cycle from the head of the ROB, in program order. Commit stops at the first instruction that is not ready.
- As in the provided code, a resolved branch and a store (which writes memory in its MEM stage) leave the ROB without using a commit slot.

### Bug fixes (`exe.py`, `wb.py`, `main.py`)
1. **Two instructions starting on one unit in the same cycle.** When an instruction moved from a reservation station into a unit, the provided code also started it right away if it was issued in an earlier cycle. With wider issue, the single integer adder and the single load/store address adder could start two instructions in the same cycle (for example two `Addi` with EXE = [8, 8]). A unit now starts at most one instruction per cycle.
2. **Pipelined FP unit advanced twice.** Starting a new instruction advanced every instruction already in a pipelined FP unit a second time in the same cycle. Now only the new instruction is advanced.
3. **Wrong RAT update on broadcast.** `wb.py` always wrote the broadcast value into the RAT. If a younger instruction had already renamed the same register, that rename was lost and later instructions read an old value. Now the RAT is updated only if it still points to the broadcasting ROB entry. Without this fix, test 3 gives wrong final values at every width.
4. **Simulation stopping too early.** The main loop stopped as soon as the ROB was empty, even if the last store was still writing to memory (at width 2 this lost the final store to `Mem[32]`). The loop now also waits for the load/store unit and for instructions that are not fetched yet.

In addition, R0 is never renamed or written, because it is hardwired to 0.

## 4. Added files

In addition to the changes to the provided code, the following files and folders were added:

| File / folder | Purpose |
|---|---|
| `code/tests/` | 16 test input files: 4 programs, each at issue widths 1, 2, 3 and 4 (for example `test1_loop_w2.txt`). |
| `code/results/` | The output of every test run, **one file per run** (for example `results/test1_loop_w2.out`). Each file has the timing table, total cycles, registers and memory. |
| `code/run_tests.py` | Runs all 16 tests, saves each output into `results/`, and checks the final registers and memory against the reference interpreter. |
| `code/reference_check.py` | A simple reference interpreter that runs a program one instruction at a time with no pipeline. It gives the correct final registers and memory to compare against. |
| `README.md` | How to run the simulator and the tests, the input format, and what each file does. |
| `report.md`, `report.pdf`, `report.tex`, `references.bib` | This report. |


## 5. How to run and where results are saved

Run one input file (the output is printed on the screen):
```
cd code
python3 main.py                              # runs test_case.txt
python3 main.py tests/test1_loop_w2.txt      # runs another input file
python3 main.py > output_w1.txt              # saves the output to a file
```

Run all tests:
```
cd code
python3 run_tests.py
```
This prints one line per run with the total cycles and whether the final state is correct, and saves each run's full output to `results/<test>_w<width>.out`.

## 6. Test cases

| Test | What it checks |
|---|---|
| `test1_loop` | The provided test case: loads, an FP multiply and add, a store, and a loop with `Bne`. |
| `test2_dependencies` | Dependencies between instructions issued in the same cycle, renaming the same register (R5) twice, and a write to R0. |
| `test3_memory_branches` | Store-to-load forwarding, `Beq` taken and not taken plus a `Bne` loop, small reservation stations, and lower-case input with commas. |
| `test4_small_rob` | A ROB with only 4 entries and 2-entry reservation stations, so issue has to stall when they are full. |

**Verification.** For every run, `run_tests.py` compares the simulator's final registers and memory with the result of `reference_check.py`. All 16 output tables were also checked automatically: instructions issue in program order, there are at most N issues and N commits per cycle, at most one CDB broadcast per cycle, and no unit starts two instructions in the same cycle.

## 7. Results

### All test runs

Output of `python3 run_tests.py`:
```
test1_loop_w1                cycles=  38   final state CORRECT
test1_loop_w2                cycles=  35   final state CORRECT
test1_loop_w3                cycles=  36   final state CORRECT
test1_loop_w4                cycles=  36   final state CORRECT
test2_dependencies_w1        cycles=  36   final state CORRECT
test2_dependencies_w2        cycles=  31   final state CORRECT
test2_dependencies_w3        cycles=  30   final state CORRECT
test2_dependencies_w4        cycles=  29   final state CORRECT
test3_memory_branches_w1     cycles=  41   final state CORRECT
test3_memory_branches_w2     cycles=  37   final state CORRECT
test3_memory_branches_w3     cycles=  40   final state CORRECT
test3_memory_branches_w4     cycles=  40   final state CORRECT
test4_small_rob_w1           cycles=  24   final state CORRECT
test4_small_rob_w2           cycles=  21   final state CORRECT
test4_small_rob_w3           cycles=  21   final state CORRECT
test4_small_rob_w4           cycles=  21   final state CORRECT
```

### Total cycles by issue width

| Test | Width 1 | Width 2 | Width 3 | Width 4 |
|---|---|---|---|---|
| test1_loop | 38 | 35 | 36 | 36 |
| test2_dependencies | 36 | 31 | 30 | 29 |
| test3_memory_branches | 41 | 37 | 40 | 40 |
| test4_small_rob | 24 | 21 | 21 | 21 |

Going from width 1 to width 2 saved 3 to 5 cycles in every test. Wider than 2 helped only in test 2.

### Example 1: the provided test case (`test1_loop`)

Width 1 (one instruction issues per cycle):
```
                              ISSUE          EXE            MEM            WB             COMMIT
Ld F2 0(R1)                   [1]            [2, 2]         [3, 7]         [9]            [10]
Mult.d F4 F2 F20              [2]            [10, 24]       []             [25]           [26]
Ld F6 0(R2)                   [3]            [4, 4]         [8, 12]        [14]           [27]
Add.d F6 F4 F6                [4]            [26, 29]       []             [30]           [31]
Sd F6 0(R2)                   [5]            [6, 6]         [32, 36]       []             [32]
Addi R1 R1 -4                 [6]            [7, 7]         []             [8]            [33]
Addi R2 R2 -4                 [7]            [8, 8]         []             [10]           [34]
Bne R1 R0 -12                 [8]            [9, 9]         []             []             []
Addi R1 R1 -4                 [10]           [11, 11]       []             [12]           [35]
Addi R2 R2 -4                 [11]           [12, 12]       []             [13]           [36]
Bne R1 R0 -12                 [12]           [13, 13]       []             []             []
Addi R1 R1 -4                 [14]           [15, 15]       []             [16]           [37]
Addi R2 R2 -4                 [15]           [16, 16]       []             [17]           [38]
Bne R1 R0 -12                 [16]           [17, 17]       []             []             []
Add.d F20 F2 F2               [18]           [19, 22]       []             [23]           [39]
```

Width 4 (four instructions issue in cycle 1 and four in cycle 2; after each `Bne` resolves, the loop body issues together):
```
                              ISSUE          EXE            MEM            WB             COMMIT
Ld F2 0(R1)                   [1]            [2, 2]         [3, 7]         [9]            [10]
Mult.d F4 F2 F20              [1]            [10, 24]       []             [25]           [26]
Ld F6 0(R2)                   [1]            [3, 3]         [8, 12]        [14]           [26]
Add.d F6 F4 F6                [1]            [26, 29]       []             [30]           [31]
Sd F6 0(R2)                   [2]            [4, 4]         [32, 36]       []             [32]
Addi R1 R1 -4                 [2]            [3, 3]         []             [4]            [33]
Addi R2 R2 -4                 [2]            [4, 4]         []             [5]            [33]
Bne R1 R0 -12                 [2]            [5, 5]         []             []             []
Addi R1 R1 -4                 [6]            [7, 7]         []             [8]            [33]
Addi R2 R2 -4                 [6]            [8, 8]         []             [10]           [33]
Bne R1 R0 -12                 [6]            [9, 9]         []             []             []
Addi R1 R1 -4                 [10]           [11, 11]       []             [12]           [34]
Addi R2 R2 -4                 [10]           [12, 12]       []             [13]           [34]
Bne R1 R0 -12                 [10]           [13, 13]       []             []             []
Add.d F20 F2 F2               [14]           [15, 18]       []             [19]           [34]
```
The final values are the same at all four widths: R2 = 20, F2 = 1.0, F4 = 3.0, F6 = 7.0, F20 = 2.0 and Mem[32] = 7.0.

### Example 2: dependencies in the same issue group (`test2_dependencies`, width 4)

`Add R5 R3 R4` issues in the same cycle as the two `Addi` instructions it depends on, and correctly waits for both results: its EX starts in cycle 5, after R4 is broadcast in cycle 4. `Add R7 R6 R5` reads the newer R5 from `Addi R5 R5 100`, not the older one.
```
                              ISSUE          EXE            MEM            WB             COMMIT
Addi R3 R0 5                  [1]            [2, 2]         []             [3]            [4]
Addi R4 R0 7                  [1]            [3, 3]         []             [4]            [5]
Add R5 R3 R4                  [1]            [5, 5]         []             [6]            [7]
Sub R6 R5 R3                  [1]            [8, 8]         []             [9]            [10]
Add.d F3 F1 F2                [2]            [3, 6]         []             [7]            [10]
Mult.d F4 F3 F2               [2]            [8, 22]        []             [23]           [24]
Sub.d F5 F4 F1                [2]            [24, 27]       []             [28]           [29]
Addi R5 R5 100                [2]            [7, 7]         []             [8]            [29]
Add R7 R6 R5                  [3]            [10, 10]       []             [11]           [29]
Addi R0 R0 9                  [3]            [4, 4]         []             [5]            [29]
Add R8 R0 R7                  [3]            [12, 12]       []             [13]           [30]
```

### Example 3: structural stalls with a 4-entry ROB (`test4_small_rob`)

At width 4 the issue cycles are 1, 1, 1, 1, 4, 6, 12, 12. Four instructions fill the ROB in cycle 1, and later instructions issue only when older ones commit and free a ROB entry. At width 1 the issue cycles are 1, 2, 3, 4, 5, 8, 14, 15.

All 16 full output tables are in the `results/` folder.

## 8. Discussion

- Wider issue helps mostly by filling the reservation stations sooner, so independent instructions start earlier. For example, in test 2 `Add.d F3` starts EX in cycle 3 at width 4 instead of cycle 6 at width 1.
- Beyond width 2 the gain is small, because the machine still has **one CDB**, one unit of each type, one memory port, and fetching stops at every branch. The 15-cycle FP multiply on the critical path also limits the total time.
- In tests 1 and 3, widths 3 and 4 are 1 to 3 cycles **slower** than width 2. The reason is the shared CDB and memory port. In test 1 at width 3, an `Addi` finishes earlier and takes the CDB in cycle 8, so the first `Ld` (which the 15-cycle multiply waits for) broadcasts in cycle 9 instead of cycle 8, and every later instruction moves back one cycle. The CDB serves results in the order they finish, not oldest first, so having more instructions in flight can delay one on the critical path.

## 9. What works and what does not

**What works:** issue width 1–4 read from the input file, in-order multi-issue with renaming inside one issue group, structural stalls when the ROB, reservation stations or load/store queue are full, multi-commit, `Bne` and `Beq`, store-to-load forwarding, and correct final registers and memory for all 16 test runs.

**Limitations** (inherited from the provided code):
- **No branch prediction or BTB.** The provided code stops fetching at every branch until it resolves, so the 1-bit predictor, the 8-entry BTB and misprediction recovery (RAT recovery and ROB squash) described in the assignment are not implemented.
- Branch targets follow the provided code's rule, target = PC + 1 + offset/4, with the offset in bytes. So `Bne R1 R0 -12` jumps back 3 instructions.
- Stores write memory in their MEM stage (recorded as their commit cycle) instead of exactly at ROB commit, and they do not use a commit slot. Since nothing executes speculatively, this does not change the results.
- There is only one CDB, so at most one result is broadcast per cycle. This limits the speed-up from wider issue.
- The number of functional units per type is read from the input file, but only one unit of each type is simulated.

## 10. Conclusion

In-order multi-issue (widths 1–4) was added to the Tomasulo simulator, four bugs in the provided code that affected multi-issue were fixed, and the implementation was tested with 4 programs at 4 widths. All 16 runs give the correct final registers and memory, and width 1 matches the original simulator exactly. Issuing 2 instructions per cycle saved 3 to 5 cycles in every test, but wider issue gave little or no further benefit, because the single CDB, the single units and the branch stalls become the bottleneck.

## 11. Code used and references

- The simulator code (`tomasulo-python`, by Qing, 2017) was provided by the course and is the starting point of this work. The multi-issue support, bug fixes, input parser, test cases, `reference_check.py` and `run_tests.py` were developed for this assignment.
- The algorithm follows Tomasulo [1], with the ROB-based speculative version described in Hennessy, Patterson and Kozyrakis [2].

**References**

1. R. M. Tomasulo, "An Efficient Algorithm for Exploiting Multiple Arithmetic Units," *IBM Journal of Research and Development*, vol. 11, no. 1, pp. 25–33, 1967. https://doi.org/10.1147/rd.111.0025
2. J. L. Hennessy, D. A. Patterson and C. Kozyrakis, *Computer Architecture: A Quantitative Approach*, 7th ed., Morgan Kaufmann, 2025. https://shop.elsevier.com/books/computer-architecture/hennessy/978-0-443-15406-5
