# NEW: recovery after a branch misprediction.
# Called right after the EX stage of cycle n, when a branch was found to be
# mispredicted. It removes every instruction issued after that branch (the
# wrong path) and restores the RAT. Fetching restarts from the correct
# address in cycle n+2 (the squash itself takes one cycle, n+1).

def squash(branch_tag, correct_pc, cycle, PC, ROB, reg_int, reg_fp,
           rat_int, rat_fp, rs_int_adder, rs_fp_adder, rs_fp_multi,
           fu_int_adder, fu_fp_adder, fu_fp_multi,
           ld_sd_queue, ld_sd_exe, ld_sd_mem, results_buffer, cdb):
    # 1. find the branch in the ROB; everything after it is on the wrong path
    pos = -1
    for i in range(len(ROB)):
        if ROB[i].ROB_tag == branch_tag:
            pos = i
            break
    if pos < 0:
        return
    branch = ROB[pos]
    wrong = set(ROB[i].ROB_tag for i in range(pos+1, len(ROB)))

    # 2. clear ROB entries after the branch
    while len(ROB) > pos + 1:
        ROB.pop()

    # 3. clear reservation stations of wrong-path instructions
    for rs in [rs_int_adder, rs_fp_adder, rs_fp_multi]:
        for entry in rs:
            if (entry.busy == 1) and (entry.dest_tag in wrong):
                entry.busy = 0

    # 4. remove wrong-path instructions from the functional units
    for fu in [fu_int_adder, fu_fp_adder, fu_fp_multi]:
        for element in list(fu):
            if element.dest_tag in wrong:
                fu.remove(element)

    # 5. load/store unit: address adder, memory port and queue
    if ld_sd_exe.busy == 1:
        for element in ld_sd_queue:
            if element.ld_sd_tag == ld_sd_exe.dest_tag:
                if element.dest_tag in wrong:
                    ld_sd_exe.busy = 0
                break
    # only a LOAD in the memory stage can be on the wrong path; a store there
    # has already committed (stores go to memory only at the ROB head), and
    # its ROB tag may already be reused by a wrong-path instruction
    if (ld_sd_mem.busy == 1) and (ld_sd_mem.op == 'Ld') and (ld_sd_mem.dest_tag in wrong):
        ld_sd_mem.busy = 0
    for element in list(ld_sd_queue):
        if element.dest_tag in wrong:
            ld_sd_queue.remove(element)

    # 6. results waiting for the CDB
    for element in list(results_buffer):
        if element.dest_tag in wrong:
            results_buffer.remove(element)
    cdb.slots = [slot for slot in cdb.slots if slot.dest_tag not in wrong]
    cdb.valid = 1 if len(cdb.slots)>0 else 0

    # 7. restore the RAT from the copy saved when the branch was issued.
    # A tag in the copy may belong to an older instruction that has already
    # broadcast (use its value) or already committed (use the register file).
    for rat, saved, regs in [(rat_int, branch.rat_int_copy, reg_int),
                             (rat_fp, branch.rat_fp_copy, reg_fp)]:
        for r in range(len(rat)):
            value = saved[r]
            if type(value) == str:
                owner = None
                for entry in ROB:
                    if entry.ROB_tag == value:
                        owner = entry
                        break
                if owner is None:
                    value = regs[r]
                elif len(owner.cdb) != 0:
                    value = owner.value
            rat[r] = value

    # 8. fetch from the correct address, starting in cycle n+2
    PC.PC = correct_pc
    PC.resume = cycle + 2
