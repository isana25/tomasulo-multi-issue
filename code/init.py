# Qing 
# 21st May 2017 

from collections import namedtuple

'''define data types'''
# reservation station 
def rs_entry():
    rs_entry = namedtuple('rs_entry', 'busy, op, tag_1st, value_1st, valid_1st, tag_2nd, value_2nd, valid_2nd, dest_tag')
    temp = rs_entry
    return temp 
# functional unit 
def fu_entry():
    fu_entry = namedtuple('fu_entry', 'cycle, op, value1, value2, dest_tag')
    temp = fu_entry
    return temp
# function result 
def fu_result():
    fu_result = namedtuple('fu_result', 'value, dest_tag')
    temp = fu_result
    return temp
# ld/sd entry
def ld_sd_entry():
    ld_sd_entry = namedtuple('ld_sd_entry', 'ld_sd_tag, ready, op, address, data, dest_tag, immediate, reg_tag, reg_value, valid')
    temp = ld_sd_entry
    return temp
# ld/sd exe
def ld_sd_exe():
    ld_sd_exe = namedtuple('ld_sd_exe', 'busy, cycle, value1, value2, dest_tag')
    temp = ld_sd_exe
    return temp
# ld/sd mem
def ld_sd_mem():
    ld_sd_mem = namedtuple('ld_sd_mem', 'busy, cycle, op, data, address, dest_tag')
    temp = ld_sd_mem
    return temp
# cdb
def cdb():
    cdb = namedtuple('cdb', 'valid, value, dest_tag')
    temp = cdb
    return temp
# ROB_entry 
def ROB_entry():
    ROB_entry = namedtuple('ROB_entry', 'ROB_tag, PC, value, dest_tag, issue, exe, mem, cdb, commit')
    temp = ROB_entry
    temp.issue = []
    temp.exe = []
    temp.mem = []
    temp.cdb = []
    temp.commit =[]
    return temp
# PC 
def PC():
    PC = namedtuple('PC', 'PC, valid')
    temp = PC
    return temp
# function: read instructions
def read_instruction(codefile):
    with open(codefile) as f:
            instructions = f.read().splitlines()
    return instructions
# ---------------------------------------------------------------
# NEW (multi-issue assignment): read the whole input file
# (hardware config + "Issue width = N" + initial regs/memory + code)
# ---------------------------------------------------------------
KNOWN_OPS = ['ld', 'sd', 'add', 'addi', 'sub', 'add.d', 'sub.d',
             'mult.d', 'bne', 'beq']

def normalize_instruction(line):
    # "add.d f1, f2, f3" -> "Add.d F1 F2 F3"  (input is case insensitive)
    tokens = line.replace(',', ' ').split()
    op = tokens[0].capitalize()          # ld->Ld, mult.d->Mult.d
    rest = [t.upper() for t in tokens[1:]]
    return ' '.join([op] + rest)

def parse_input(path):
    config = {
        'int_adder': {'rs': 2, 'ex': 1, 'fu': 1},
        'fp_adder':  {'rs': 3, 'ex': 3, 'fu': 1},
        'fp_multi':  {'rs': 2, 'ex': 20, 'fu': 1},
        'ld_sd':     {'rs': 3, 'ex': 1, 'mem': 4, 'fu': 1},
        'rob': 64,
        'issue_width': 1,                # default issue width = 1
    }
    reg_int = [0] * 32
    reg_fp = [0.0] * 32
    memory = [0] * 256
    instructions = []
    units = {'integer adder': 'int_adder', 'fp adder': 'fp_adder',
             'fp multiplier': 'fp_multi', 'load/store unit': 'ld_sd'}
    with open(path) as f:
        lines = f.read().splitlines()
    for raw in lines:
        line = raw.strip()
        low = line.lower()
        if line == '' or low.startswith('#'):
            continue
        # hardware table rows
        unit = None
        for name in units:
            if low.startswith(name):
                unit = units[name]
                nums = [int(x) for x in low[len(name):].split()]
                break
        if unit is not None:
            if unit == 'ld_sd':       # rs, ex, mem, fu
                config[unit] = {'rs': nums[0], 'ex': nums[1],
                                'mem': nums[2], 'fu': nums[3]}
            else:                     # rs, ex, fu
                config[unit] = {'rs': nums[0], 'ex': nums[1], 'fu': nums[2]}
            continue
        if low.startswith('rob entries'):
            config['rob'] = int(low.split('=')[1])
            continue
        if low.startswith('issue width'):
            width = int(low.split('=')[1])
            config['issue_width'] = max(1, min(4, width))   # 1..4
            continue
        # instruction?
        first = low.replace(',', ' ').split()[0]
        if first in KNOWN_OPS:
            instructions.append(normalize_instruction(line))
            continue
        # initial values: "R1=12, R2=32, F20=3.0" / "Mem[4]=3.0, ..."
        if '=' in line:
            for item in line.split(','):
                if '=' not in item:
                    continue
                name, value = [x.strip() for x in item.split('=')]
                name = name.upper()
                if name.startswith('MEM['):
                    memory[int(name[4:-1])] = float(value)
                elif name.startswith('R'):
                    reg_int[int(name[1:])] = int(float(value))
                elif name.startswith('F'):
                    reg_fp[int(name[1:])] = float(value)
    reg_int[0] = 0   # R0 is hardwired to 0
    return config, reg_int, reg_fp, memory, instructions

# function: build rs
def build_rs(num):
    rs = []
    for _ in range(num):
        temp = rs_entry()
        temp.busy = 0
        rs.extend([temp])
    return rs