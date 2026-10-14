# Runs every test in tests/ with main.py, saves each output to results/
# (one file per run), and checks every run automatically:
#   1. final registers and memory = reference interpreter (reference_check.py)
#   2. timing rules of the machine (see check_timing below)
import os, subprocess, glob, ast, collections
from init import parse_input
from reference_check import run_reference

UNIT = {'Add': 'int', 'Addi': 'int', 'Sub': 'int', 'Bne': 'int', 'Beq': 'int',
        'Add.d': 'fp_add', 'Sub.d': 'fp_add', 'Mult.d': 'fp_mul',
        'Ld': 'ldsd', 'Sd': 'ldsd'}

def final_state(text):
    R, F, M = {}, {}, {}
    lines = text.splitlines()
    i = lines.index('REGISTER VALUES') + 1
    while lines[i].strip():
        names, vals = lines[i].split(), lines[i+1].split()[1:]
        for n, v in zip(names, vals):
            (R if n[0] == 'R' else F)[int(n[1:])] = float(v)
        i += 2
    j = lines.index('NON-ZERO MEMORY VALUES') + 2
    for l in lines[j:]:
        if l.strip():
            a, v = l.split(); M[int(a)] = float(v)
    return R, F, M

def timing_table(text):
    lines = text.splitlines()
    start = [k for k, l in enumerate(lines) if l.strip().startswith('ISSUE')][0] + 1
    rows = []
    for l in lines[start:]:
        if not l.strip():
            break
        cols = [ast.literal_eval(l[30+15*c:30+15*(c+1)].strip() or '[]') for c in range(5)]
        rows.append((l[:30].strip(), cols))
    return rows

def check_timing(rows, config, width):
    errors = []
    ex_time = {'int': config['int_adder']['ex'], 'fp_add': config['fp_adder']['ex'],
               'fp_mul': config['fp_multi']['ex'], 'ldsd': config['ld_sd']['ex']}
    mem_time = config['ld_sd']['mem']
    issues, wbs, commits = collections.Counter(), collections.Counter(), collections.Counter()
    starts = collections.Counter()
    busy = {'int': [], 'ldsd': [], 'mem': []}
    prev_issue, prev_commit = 0, None
    for ins, (I, E, M, W, C) in rows:
        op = ins.split()[0]; unit = UNIT[op]
        # in-order issue
        if I[0] < prev_issue:
            errors.append(ins + ': issued out of order')
        prev_issue = I[0]
        issues[I[0]] += 1
        # stage order and EX length
        if E[0] <= I[0]:
            errors.append(ins + ': EX starts in its issue cycle')
        if E[1] - E[0] + 1 != ex_time[unit]:
            errors.append(ins + ': EX takes ' + str(E[1]-E[0]+1) + ' cycles')
        starts[(unit, E[0])] += 1
        if unit in ('int', 'ldsd'):          # unpipelined units
            busy[unit].append((E[0], E[1], ins))
        if len(M) == 2:                       # memory access (not forwarded)
            if M[1] - M[0] + 1 != mem_time:
                errors.append(ins + ': MEM takes ' + str(M[1]-M[0]+1) + ' cycles')
            if M[0] <= E[1]:
                errors.append(ins + ': MEM starts before EX ends')
            busy['mem'].append((M[0], M[1], ins))
        if len(M) == 1 and M[0] <= E[1]:
            errors.append(ins + ': forwarded in its EX cycle')
        for w in W:
            wbs[w] += 1
        if W:
            commits[C[0]] += 1
        # a store writes memory only after the instruction before it committed
        if op == 'Sd' and prev_commit is not None and M[0] < prev_commit:
            errors.append(ins + ': store writes memory before older instruction commits')
        if C:
            prev_commit = C[0]
    for (unit, cyc), n in starts.items():
        if n > 1:
            errors.append(unit + ' unit starts ' + str(n) + ' instructions in cycle ' + str(cyc))
    for name, spans in busy.items():
        spans.sort()
        for a, b in zip(spans, spans[1:]):
            if b[0] <= a[1]:
                errors.append(name + ' unit used by two instructions at once: ' + a[2] + ' / ' + b[2])
    for c, n in issues.items():
        if n > width: errors.append(str(n) + ' issues in cycle ' + str(c))
    for c, n in commits.items():
        if n > width: errors.append(str(n) + ' commits in cycle ' + str(c))
    for c, n in wbs.items():
        if n > 1: errors.append(str(n) + ' CDB broadcasts in cycle ' + str(c))
    return errors

os.makedirs('results', exist_ok=True)
all_ok = True
for path in sorted(glob.glob('tests/*.txt')):
    name = os.path.basename(path)[:-4]
    out = subprocess.run(['python3', 'main.py', path], capture_output=True, text=True, timeout=300)
    text = out.stdout + out.stderr
    open('results/' + name + '.out', 'w').write(text)
    try:
        config = parse_input(path)[0]
        R, F, M = final_state(text)
        rR, rF, rM = run_reference(path)
        state_ok = all(abs(R[i]-rR[i]) < 1e-9 and abs(F[i]-rF[i]) < 1e-9 for i in range(32)) \
                   and M == {a: float(v) for a, v in enumerate(rM) if v != 0}
        errors = check_timing(timing_table(text), config, config['issue_width'])
        cycles = [l for l in text.splitlines() if l.startswith('Total cycles')][0].split()[-1]
    except Exception as e:
        state_ok, errors, cycles = False, ['ERROR ' + repr(e)], '?'
    ok = state_ok and not errors
    all_ok = all_ok and ok
    print(f'{name:28s} cycles={cycles:>4}   final state {"CORRECT" if state_ok else "WRONG"}'
          f'   timing {"OK" if not errors else "FAILED"}')
    for e in errors[:5]:
        print('      ' + e)
print('ALL TESTS PASSED' if all_ok else 'SOME TESTS FAILED')