# Reference interpreter: runs the program one instruction at a time
# (no pipeline) and returns the correct final registers and memory.
# Used to check the simulator gives the same results for every issue width.
import sys
from init import parse_input

def run_reference(path):
    config, R, F, M, code = parse_input(path)
    pc, steps = 0, 0
    while pc < len(code) and steps < 100000:
        t = code[pc].split(' '); op = t[0]; steps += 1
        nxt = pc + 1
        if op in ('Ld', 'Sd'):
            off, reg = t[2][:-1].split('(')
            addr = R[int(reg[1:])] + int(off)
            if op == 'Ld': F[int(t[1][1:])] = M[addr]
            else:          M[addr] = F[int(t[1][1:])]
        elif op in ('Bne', 'Beq'):
            a, b = R[int(t[1][1:])], R[int(t[2][1:])]
            taken = (a != b) if op == 'Bne' else (a == b)
            if taken: nxt = int(pc + 1 + int(t[3]) / 4)   # same offset rule as the simulator
        else:
            src = lambda x: (R if x[0] == 'R' else F)[int(x[1:])]
            a = src(t[2]); b = int(t[3]) if op == 'Addi' else src(t[3])
            v = a + b if op in ('Add', 'Addi', 'Add.d') else (a - b if op in ('Sub', 'Sub.d') else a * b)
            d = t[1]
            if d[0] == 'R':
                if d != 'R0': R[int(d[1:])] = v
            else: F[int(d[1:])] = v
        pc = nxt
    return R, F, M

if __name__ == '__main__':
    R, F, M = run_reference(sys.argv[1])
    print('R', [(i, v) for i, v in enumerate(R) if v != 0])
    print('F', [(i, v) for i, v in enumerate(F) if v != 0])
    print('M', [(i, v) for i, v in enumerate(M) if v != 0])
