# Qing 
# 29th may 2017
'''
1. commit ROB_buffer
2. fetch header into ROB_buffer
'''

# function: print ROB entry 
def print_ROB(entry, instructions):
    item = instructions[entry.PC].ljust(30)
    item += str(entry.issue).ljust(15) 
    item += str(entry.exe).ljust(15) 
    item += str(entry.mem).ljust(15)
    item += str(entry.cdb).ljust(15)
    item += str(entry.commit)
    print(item)
# function: modify architectual reg
def modify_arch_reg(entry, reg_int, reg_fp):
    if entry.dest_tag[0] == 'F':
        reg_fp[int(entry.dest_tag[1:])] = entry.value
    elif (entry.dest_tag[0] == 'R') & (entry.dest_tag != 'R0'):  # R0 stays 0
        reg_int[int(entry.dest_tag[1:])] = entry.value
    else:
        pass

# function: commit
# MODIFIED for multi-issue: commit up to issue_width instructions per
# cycle from the ROB head, in order, stopping at the first one not ready.
# As in the original single-issue code, a resolved branch and a store that
# already went to memory leave the ROB without using a commit slot.
def commit(ROB, reg_int, reg_fp, cycle, instructions, issue_width=1):
    committed = 0
    while (len(ROB)>0) & (committed<issue_width):
        op = instructions[ROB[0].PC].split(' ')[0]
        if (op=='Bne')|(op=='Beq'):
            if len(ROB[0].exe)!=0:      # branch resolved
                entry = ROB.popleft()
                print_ROB(entry, instructions)
                continue
            break
        if len(ROB[0].cdb)!=0:          # broadcasted instructions
            ROB[0].commit.append(cycle+1)
            entry = ROB.popleft()
            modify_arch_reg(entry, reg_int, reg_fp)
            print_ROB(entry, instructions)
            committed += 1
        elif len(ROB[0].commit)!=0:     # Sd (written to memory in MEM)
            entry = ROB.popleft()
            print_ROB(entry, instructions)
        else:                           # head not ready -> stop (in order)
            break