# Qing 
# 24th May 2017

''' 
1. calculate valid instructions
    -- for ALU instructions, write results into fu_results, remove that fu entry  
    -- for LD/SD, write address result immediately back to ld_sd_queue
2. fetch instructions into function unit with spare space
    -- remove ALU instructions from rs
    -- don't remove ld/sd instructions
'''
from init import fu_entry, fu_result
from predictor import update

# function: check rs and return valid instruction index
def check_valid_ins_in_rs(rs):
    index = -1
    if len(rs)!=0:
        for i in range(len(rs)):
            if (rs[i].valid_1st==1)&(rs[i].valid_2nd==1)&(rs[i].busy==1):
                index = i
                break
    return index

# NEW: return the index of the OLDEST ready instruction in a reservation
# station that was issued in an earlier cycle (-1 if none). Oldest = closest
# to the head of the ROB.
def oldest_ready_in_rs(rs, ROB, cycle):
    best, best_pos = -1, None
    for i in range(len(rs)):
        if (rs[i].busy==1)&(rs[i].valid_1st==1)&(rs[i].valid_2nd==1):
            pos = find_ROB_entry(ROB, rs[i].dest_tag)
            if ROB[pos].issue[0] < cycle:
                if (best_pos is None) or (pos < best_pos):
                    best, best_pos = i, pos
    return best

# function: check ld_sd_queue and return valid instruction index
def check_valid_ins_in_ldsd(ldsd):
    index = -1
    if len(ldsd)!=0:
        for i in range(len(ldsd)):
            if (ldsd[i].valid==1) & (ldsd[i].ready==0):
                index = i
                break
    return index

# function: add entry into fu 
def add_entry_into_fu(fu, ins_in_rs):
    fu[-1].cycle = 0
    fu[-1].op = ins_in_rs.op
    fu[-1].value1 = ins_in_rs.value_1st
    fu[-1].value2 = ins_in_rs.value_2nd
    fu[-1].dest_tag = ins_in_rs.dest_tag

# function: find ROB entry by tag
def find_ROB_entry(ROB, tag):
    for index in range(len(ROB)):
        if ROB[index].ROB_tag == tag:
            break
    return index

# function: functional units execution 
# MODIFIED: only_new=True advances ONLY the instruction that was just put
# into the unit. Before, the whole pipelined unit was advanced a second
# time in the same cycle, so older instructions finished too early.
def fu_exe(fu, fu_results, ROB, time_fu, cycle, PC, only_new=False):
    if len(fu)!=0:
        if only_new:
            fu[-1].cycle += 1
        else:
            for element in fu:
                element.cycle += 1
    started = False
    if len(fu)!=0:
        # write starting cycle 
        if fu[-1].cycle == 1:
            started = True
            index = find_ROB_entry(ROB, fu[-1].dest_tag)
            ROB[index].exe.append(cycle)
        # finish cycle
        if fu[0].cycle == time_fu:
            index = find_ROB_entry(ROB, fu[0].dest_tag)
            ROB[index].exe.append(cycle)
            # calculation result
            fu_results.append(fu_result())
            fu_results[-1].dest_tag = fu[0].dest_tag
            if (fu[0].op=='Add')|(fu[0].op=='Add.d')|(fu[0].op=='Addi'):
                fu_results[-1].value = fu[0].value1 + fu[0].value2
            elif (fu[0].op=='Sub')|(fu[0].op=='Sub.d'):
                fu_results[-1].value = fu[0].value1 - fu[0].value2
            elif (fu[0].op=='Mult.d'):
                fu_results[-1].value = fu[0].value1 * fu[0].value2
            elif (fu[0].op=='Bne')|(fu[0].op=='Beq'):   # MODIFIED: Beq
                fu_results.pop()
                if fu[0].op=='Bne':
                    taken = fu[0].value1 != fu[0].value2
                else:
                    taken = fu[0].value1 == fu[0].value2
                # MODIFIED (branch prediction): compare the real outcome with
                # the prediction, update the BTB, and flag a misprediction
                index = find_ROB_entry(ROB, fu[0].dest_tag)
                branch_pc = ROB[index].PC
                offset = ROB[index].dest_tag
                target = int(branch_pc + 1 + offset/4)
                actual_next = target if taken else branch_pc + 1
                update(PC.btb, branch_pc, taken, target)
                if actual_next != ROB[index].pred_next:
                    PC.mispredict = (fu[0].dest_tag, actual_next)
            else:
                pass
            # remove from fu 
            fu.popleft()
    return started

# function: ld_sd_execution 
# MODIFIED: returns True if it started an address calculation this cycle
def ld_sd_execution(ld_sd_exe, time_ld_sd_exe, ld_sd_queue, ROB, cycle):
    started = False
    if ld_sd_exe.busy == 1:
        # write down starting cycle
        if ld_sd_exe.cycle == 0:            
            started = True
            for element in ld_sd_queue:
                if element.ld_sd_tag == ld_sd_exe.dest_tag:
                    break
            index = find_ROB_entry(ROB, element.dest_tag)
            ROB[index].exe.append(cycle)
        # execute (MODIFIED: the counter now advances every cycle; before,
        # it only advanced in the first cycle, so an address calculation with
        # more than 1 EX cycle never finished)
        ld_sd_exe.cycle += 1
        # write address back to ld_sd_queue
        if ld_sd_exe.cycle == time_ld_sd_exe:
            address = ld_sd_exe.value1 + ld_sd_exe.value2
            for element in ld_sd_queue:
                if element.ld_sd_tag == ld_sd_exe.dest_tag:
                    element.address = address
                    element.ready = 1
                    break
            # write down finish cycle
            index = find_ROB_entry(ROB, element.dest_tag)
            ROB[index].exe.append(cycle)
            ld_sd_exe.busy = 0
    return started

# function: execution
def exe(fu_int_adder, time_fu_int_adder,
        fu_fp_adder, time_fu_fp_adder,
        fu_fp_multi, time_fu_fp_multi, results_buffer,
        rs_int_adder, rs_fp_adder, rs_fp_multi, 
        ld_sd_exe, time_ld_sd_exe, ld_sd_queue,
        cycle, ROB, PC):
    '''execution in fu and ld_sd address calculation'''
    busy_ldsd = ld_sd_exe.busy == 1      # address adder (unpipelined) in use this cycle
    started_ldsd = ld_sd_execution(ld_sd_exe, time_ld_sd_exe, ld_sd_queue, ROB, cycle) 
    # functional units 
    # MODIFIED: remember if a unit already started an instruction this cycle;
    # a unit may start at most ONE instruction per cycle
    busy_int = len(fu_int_adder) > 0      # unpipelined integer adder in use this cycle
    started_int = fu_exe(fu_int_adder, results_buffer, ROB, time_fu_int_adder, cycle, PC)
    started_fp_add = fu_exe(fu_fp_adder, results_buffer, ROB, time_fu_fp_adder, cycle, PC)
    started_fp_mul = fu_exe(fu_fp_multi, results_buffer, ROB, time_fu_fp_multi, cycle, PC)
    '''fetch instructions from rs and ld_sd_queue'''
    # from ld_sd_queue
    # check valid ins in ld_sd_queue 
    index = check_valid_ins_in_ldsd(ld_sd_queue)
    # put ins into ld_sd_exe
    if (index>=0)&(ld_sd_exe.busy==0):
        ld_sd_exe.busy = 1
        ld_sd_exe.cycle = 0
        ld_sd_exe.value1 = ld_sd_queue[index].reg_value
        ld_sd_exe.value2 = ld_sd_queue[index].immediate
        ld_sd_exe.dest_tag = ld_sd_queue[index].ld_sd_tag
        # MODIFIED: only start now if the address adder had no other Ld/Sd
        # in it this cycle (it is unpipelined); otherwise it starts next cycle
        if (ROB[find_ROB_entry(ROB, ld_sd_queue[index].dest_tag)].issue[0] < cycle) & (not busy_ldsd):
            ld_sd_execution(ld_sd_exe, time_ld_sd_exe, ld_sd_queue, ROB, cycle)
    # from rs (MODIFIED)
    # An instruction leaves its reservation station only when it can start
    # executing in this cycle, and the oldest ready instruction goes first.
    # int_adder: UNPIPELINED -> it starts a new instruction only if it had
    # no instruction in it at the start of this cycle
    if not busy_int:
        index = oldest_ready_in_rs(rs_int_adder, ROB, cycle)
        if index >= 0:
            fu_int_adder.append(fu_entry())
            add_entry_into_fu(fu_int_adder, rs_int_adder[index])
            fu_exe(fu_int_adder, results_buffer, ROB, time_fu_int_adder, cycle, PC, only_new=True)
            rs_int_adder[index].busy = 0
    # fp_adder: pipelined -> one new instruction per cycle
    if not started_fp_add:
        index = oldest_ready_in_rs(rs_fp_adder, ROB, cycle)
        if index >= 0:
            fu_fp_adder.append(fu_entry())
            add_entry_into_fu(fu_fp_adder, rs_fp_adder[index])
            fu_exe(fu_fp_adder, results_buffer, ROB, time_fu_fp_adder, cycle, PC, only_new=True)
            rs_fp_adder[index].busy = 0
    # fp_multi: pipelined -> one new instruction per cycle
    if not started_fp_mul:
        index = oldest_ready_in_rs(rs_fp_multi, ROB, cycle)
        if index >= 0:
            fu_fp_multi.append(fu_entry())
            add_entry_into_fu(fu_fp_multi, rs_fp_multi[index])
            fu_exe(fu_fp_multi, results_buffer, ROB, time_fu_fp_multi, cycle, PC, only_new=True)
            rs_fp_multi[index].busy = 0
