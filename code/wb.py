# Qing 
# 29th May 2017 

'''
1. broadcast data on cdb 
2. fetch data from results queue 
3. remove entry in results queue

'''
from init import fu_result

# function: find ROB entry by tag
def find_ROB_entry(ROB, tag):
    for index in range(len(ROB)):
        if ROB[index].ROB_tag == tag:
            break
    return index

# function: boroadcast
# rat_int, rat_fp, reservation stations, ld_sd_queue, ROB
def boroadcast(cdb, rat_int, rat_fp, 
                rs_int_adder, rs_fp_adder, rs_fp_multi,
                ld_sd_queue, ROB, cycle):
    # dest_tag
    dest_tag = cdb.dest_tag
    index = find_ROB_entry(ROB, dest_tag)
    reg_tag = ROB[index].dest_tag
    # MODIFIED: only clear the RAT entry if it still points to THIS ROB tag.
    # If a younger instruction renamed the register in the meantime (very
    # common with multi-issue), the RAT must keep pointing to the younger one.
    # rat_int
    if (type(reg_tag)==str) and (reg_tag[0] == 'R'):
        if rat_int[int(reg_tag[1:])] == dest_tag:
            rat_int[int(reg_tag[1:])] = cdb.value
    # rat_fp
    if (type(reg_tag)==str) and (reg_tag[0] == 'F'):
        if rat_fp[int(reg_tag[1:])] == dest_tag:
            rat_fp[int(reg_tag[1:])] = cdb.value 
    # rs list
    rs_list = [rs_int_adder, rs_fp_adder, rs_fp_multi]
    for rs in rs_list:
        for element in rs:
            if (element.tag_1st==dest_tag)&(element.valid_1st==0):
                element.value_1st = cdb.value
                element.valid_1st = 1
            if (element.tag_2nd==dest_tag)&(element.valid_2nd==0):
                element.value_2nd = cdb.value
                element.valid_2nd = 1
    # ld_sd_queue 
    for element in ld_sd_queue:
        if (element.data==dest_tag)&(element.op=='Sd'):
            element.data = cdb.value
        if (element.reg_tag==dest_tag)&(element.valid==0):
            element.reg_value = cdb.value
            element.valid = 1
    # ROB
    for element in ROB:
        if element.ROB_tag == dest_tag:
            element.value = cdb.value
            element.cdb.append(cycle)

# function: wb 
# MODIFIED (multiple write-backs): up to issue_width results are written back
# (broadcast) per cycle, the same number as issued and committed per cycle.
# cdb.slots holds the results that were put on the bus in the previous cycle.
def wb(cdb, rat_int, rat_fp, 
        rs_int_adder, rs_fp_adder, rs_fp_multi,
        ld_sd_queue, ROB, cycle,
        results_buffer, issue_width=1):
    # broadcast every result that is on the bus
    for slot in cdb.slots:
        boroadcast(slot, rat_int, rat_fp, 
                    rs_int_adder, rs_fp_adder, rs_fp_multi,
                    ld_sd_queue, ROB, cycle)
    cdb.slots = []
    # fetch up to issue_width results from the results queue, oldest first
    while (len(results_buffer)>0) and (len(cdb.slots)<issue_width):
        slot = fu_result()
        slot.value = results_buffer[0].value
        slot.dest_tag = results_buffer[0].dest_tag
        cdb.slots.append(slot)
        results_buffer.popleft()
    cdb.valid = 1 if len(cdb.slots)>0 else 0
