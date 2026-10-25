# NEW: branch predictor (1-bit predictor + 8-entry BTB), as described in the
# assignment. The BTB is indexed by the least significant 3 bits of the word
# address of the branch (here: the instruction index, since each instruction
# is one word).

BTB_SIZE = 8

def build_btb():
    btb = []
    for _ in range(BTB_SIZE):
        btb.append({'valid': 0, 'pc': -1, 'target': 0, 'bit': 0})
    return btb

# predict the next PC for the branch at index pc
# - BTB hit and prediction bit = 1 (taken): go to the stored target
# - otherwise (miss, or bit = 0): predict not taken, go to pc + 1
def predict(btb, pc):
    entry = btb[pc % BTB_SIZE]
    if (entry['valid'] == 1) and (entry['pc'] == pc) and (entry['bit'] == 1):
        return True, entry['target']
    return False, pc + 1

# after the branch is resolved: remember the outcome (1 bit) and the target
def update(btb, pc, taken, target):
    entry = btb[pc % BTB_SIZE]
    entry['valid'] = 1
    entry['pc'] = pc
    entry['target'] = target
    entry['bit'] = 1 if taken else 0
