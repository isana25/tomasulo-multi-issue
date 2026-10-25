# Qing
# 21st May 2017
# MODIFIED: multi-issue support (issue width 1-4), config read from input file

import sys
from collections import deque
from init import parse_input, build_rs, ld_sd_exe, ld_sd_mem, cdb, PC
from issue import issue
from exe import exe
from mem import mem
from wb import wb
from commit import commit
from predictor import build_btb
from recovery import squash

'''input file (hardcoded; can be overridden: python3 main.py tests/xxx.txt)'''
INPUT_FILE = 'test_case.txt'
if len(sys.argv) > 1:
    INPUT_FILE = sys.argv[1]

'''initialize'''
config, reg_int, reg_fp, memory, instructions = parse_input(INPUT_FILE)
issue_width = config['issue_width']
# only 1 functional unit of each type is simulated
for unit in ['int_adder', 'fp_adder', 'fp_multi', 'ld_sd']:
    if config[unit]['fu'] != 1:
        print('WARNING: ' + unit + ' has ' + str(config[unit]['fu']) +
              ' FUs in the input file; this simulator uses 1')
rat_int = list(reg_int)
rat_fp = list(reg_fp)
'''intialize reservation stations'''
rs_int_adder = build_rs(config['int_adder']['rs'])
rs_fp_adder = build_rs(config['fp_adder']['rs'])
rs_fp_multi = build_rs(config['fp_multi']['rs'])
'''initilize function units'''
fu_int_adder = deque()
time_fu_int_adder = config['int_adder']['ex']
fu_fp_adder = deque()
time_fu_fp_adder = config['fp_adder']['ex']
fu_fp_multi = deque()
time_fu_fp_multi = config['fp_multi']['ex']
'''initialize load/store queue'''
ld_sd_queue = deque()
size_ld_sd_queue = config['ld_sd']['rs']
ld_sd_exe = ld_sd_exe()
ld_sd_exe.busy = 0
time_ld_sd_exe = config['ld_sd']['ex']
ld_sd_mem = ld_sd_mem()
ld_sd_mem.busy = 0
time_ld_sd_mem = config['ld_sd']['mem']
'''initialize ROB'''
ROB = deque()
size_ROB = config['rob']
'''initialize CDB'''
results_buffer = deque()
cdb = cdb()
cdb.valid = 0
'''instruction pointer'''
PC = PC()
PC.PC = 0
PC.valid = 1
# NEW (branch prediction)
PC.btb = build_btb()        # 8-entry BTB with 1-bit predictors
PC.resume = 0               # no fetch before this cycle (misprediction repair)
PC.mispredict = None        # (branch ROB tag, correct PC) when detected in EX
PC.branch_issued = False
cycle = 1
MAX_CYCLES = 10000   # safety stop

print('Input file: ' + INPUT_FILE + '    Issue width = ' + str(issue_width))
print('')
item = ''.ljust(30)
for title in ['ISSUE', 'EXE', 'MEM', 'WB', 'COMMIT']:
    item += title.ljust(15)
print (item)

# main loop (MODIFIED: also keep running while instructions are left to
# issue, or a store is still writing to memory; before, the program could
# stop with the ROB empty but the last Sd not yet in memory)
while ((len(ROB)>0) | (PC.PC<len(instructions)) | (ld_sd_mem.busy==1)
       | (len(ld_sd_queue)>0)) & (cycle<MAX_CYCLES):

    '''ISSUE stage: up to issue_width instructions, in order'''
    issue(cycle, PC, instructions, ROB, size_ROB,
          rs_int_adder, rs_fp_adder, rs_fp_multi,
          ld_sd_queue, size_ld_sd_queue,
          rat_int, rat_fp, issue_width, PC.btb)

    '''EXE stage'''
    exe(fu_int_adder, time_fu_int_adder,
        fu_fp_adder, time_fu_fp_adder,
        fu_fp_multi, time_fu_fp_multi, results_buffer,
        rs_int_adder, rs_fp_adder, rs_fp_multi,
        ld_sd_exe, time_ld_sd_exe, ld_sd_queue,
        cycle, ROB, PC)

    '''NEW: misprediction found in EX -> squash the wrong path'''
    if PC.mispredict is not None:
        branch_tag, correct_pc = PC.mispredict
        squash(branch_tag, correct_pc, cycle, PC, ROB, reg_int, reg_fp,
               rat_int, rat_fp, rs_int_adder, rs_fp_adder, rs_fp_multi,
               fu_int_adder, fu_fp_adder, fu_fp_multi,
               ld_sd_queue, ld_sd_exe, ld_sd_mem, results_buffer, cdb)
        PC.mispredict = None

    '''MEM stage'''
    mem(ld_sd_queue, ld_sd_mem, time_ld_sd_mem, results_buffer,
        memory, ROB, cycle)

    '''CDB stage (one CDB: one broadcast per cycle)'''
    wb(cdb, rat_int, rat_fp,
       rs_int_adder, rs_fp_adder, rs_fp_multi,
       ld_sd_queue, ROB, cycle,
       results_buffer)

    '''COMMIT stage: up to issue_width instructions, in order'''
    commit(ROB, reg_int, reg_fp, cycle, instructions, issue_width)

    cycle +=1

if cycle >= MAX_CYCLES:
    print('WARNING: stopped after ' + str(MAX_CYCLES) + ' cycles')

'''final results'''
print('')
print('Total cycles: ' + str(cycle-1))
print('')
print('REGISTER VALUES')
for name, regs in [('R', reg_int), ('F', reg_fp)]:
    for start in range(0, 32, 8):
        head = ''.ljust(8)
        vals = 'value:'.ljust(8)
        for i in range(start, start+8):
            head += (name+str(i)).ljust(8)
            vals += (str(regs[i]) + ' ').ljust(8)   # always at least one space
        print(head)
        print(vals)
print('')
print('NON-ZERO MEMORY VALUES')
print('Addresses'.ljust(15) + 'Values')
for addr in range(len(memory)):
    if memory[addr] != 0:
        print(str(addr).ljust(15) + str(memory[addr]))
