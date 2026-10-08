# Runs every test in tests/ with main.py, saves each output to results/
# (one file per run), and checks final registers/memory against the
# reference interpreter.
import os, subprocess, glob
from reference_check import run_reference

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

os.makedirs('results', exist_ok=True)
for path in sorted(glob.glob('tests/*.txt')):
    name = os.path.basename(path)[:-4]
    out = subprocess.run(['python3', 'main.py', path], capture_output=True, text=True, timeout=120)
    text = out.stdout + out.stderr
    open(f'results/{name}.out', 'w').write(text)
    try:
        R, F, M = final_state(text)
        rR, rF, rM = run_reference(path)
        ok = all(abs(R[i]-rR[i]) < 1e-9 and abs(F[i]-rF[i]) < 1e-9 for i in range(32)) \
             and M == {a: float(v) for a, v in enumerate(rM) if v != 0}
        cycles = [l for l in text.splitlines() if l.startswith('Total cycles')][0].split()[-1]
    except Exception as e:
        ok, cycles = False, 'ERROR ' + repr(e)
    print(f'{name:28s} cycles={cycles:>4}   final state {"CORRECT" if ok else "WRONG"}')
