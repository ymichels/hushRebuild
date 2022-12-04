
import random
from ORAM import ORAM
from PathORAM.path_ORAM import PathORAM
from RAM.local_RAM import local_RAM
from RAM.file_RAM import file_RAM
from config import config
from utils.helper_functions import get_random_string

#https://github.com/ymichels/hushRebuild


def path_ORAM_test():

    # Results for this:
    # RAM.RT_WRITE:  10486081
    # RAM.RT_READ:  10485760
    # RAM.BALL_WRITE:  813189040
    # RAM.BALL_READ:  796917760
    real_ram = {}
    S = 20
    path_oram = PathORAM(2**S,True)
    # path_oram.allocate_memory()
    # print(path_oram.access('write',0,b'1234'))
    # print(path_oram.access('write',1,b'1235'))
    # print(path_oram.access('read',0))
    # print(path_oram.access('read',1))
    # print(path_oram.position_map_access(0))
    # print(path_oram.position_map_access(0))
    for i in range(int((2**S)/1)):
        data = get_random_string(path_oram.conf.BALL_DATA_SIZE)
        real_ram[i] = data
        path_oram.access('write',i,data)
        if i % 1_000 == 0:
            print(i,': ',len(path_oram.local_stash))

    for i in range(2**(S)):
        if i % 1_000 == 0:
            print(i,': ',len(path_oram.local_stash))
        key = random.randint(0,2**S - 1)
        # if i < 2**S:
        #     oram_ans = path_oram.access('read', i)
        oram_ans = path_oram.access('read', key)
        if oram_ans != real_ram[key]:
            oram_ans = path_oram.access('read', key)
            oram_ans = path_oram.access('read', key)
            raise 'ERROR!'
    
    print('RAM.RT_WRITE: ', local_RAM.RT_WRITE)
    print('RAM.RT_READ: ', local_RAM.RT_READ)
    print('RAM.BALL_WRITE: ', local_RAM.BALL_WRITE)
    print('RAM.BALL_READ: ', local_RAM.BALL_READ)
    print('done!')
    # for i in range(0, 2**S):
    #     key = random.randint(0,2**(S-2) - 1)
    #     oram_ans = path_oram.access('read', key)
    #     if oram_ans != real_ram[key]:
    #         raise 'ERROR!'




#Final test
if False:
    oram_size = 2**4*config.MU
    oram = ORAM(oram_size)
    oram.cleanWriteMemory()
    oram.initial_build('testing_data.txt')
    data_ram = file_RAM('testing_data.txt', oram.conf)
    for i in range(oram_size + 50_000):
        ball_to_read = data_ram.readBall(random.randint(0,oram_size-1)*oram.conf.BALL_SIZE)
        key = ball_to_read[1 + oram.conf.BALL_STATUS_POSITION:]
        oram.access('read',key)
        if i % 10_000 == 0:
            print('accesses: ',i)
        
    print('RAM.RT_WRITE: ', file_RAM.RT_WRITE)
    print('RAM.RT_READ: ', file_RAM.RT_READ)
    print('RAM.BALL_WRITE: ', file_RAM.BALL_WRITE)
    print('RAM.BALL_READ: ', file_RAM.BALL_READ)
    print('done!')
    
    
    
#Debug test
def debug_test():
    # Results for this:
    # RAM.RT_WRITE:  5057017
    # RAM.RT_READ:  5056827
    # RAM.BALL_WRITE:  87572960
    # RAM.BALL_READ:  79399793
    oram_size = 2**3*config.MU
    oram = ORAM(oram_size)
    oram.cleanWriteMemory()
    oram.initial_build('testing_data.txt')
    # data_ram = local_RAM('testing_data.txt', oram.conf)
    o = 0
    j=0
    for i in range(oram_size + 50_000):
        ball_to_read = oram.original_data_ram.readBall(random.randint(0,oram_size-1)*oram.conf.BALL_SIZE)
        key = ball_to_read[1 + oram.conf.BALL_STATUS_POSITION:]
        read_ball = oram.access('read',key)
        j+=1
        if read_ball != ball_to_read:
            print("INACCUARE DATA!!!",read_ball,'::', ball_to_read)
        if o != oram.not_found:
            o= oram.not_found
            j=0
        if i % 10_000 == 0:
            print('accesses: ',i)
            print('not-found ratio: ', oram.not_found/(i+1))
        
    print('RAM.RT_WRITE: ', local_RAM.RT_WRITE)
    print('RAM.RT_READ: ', local_RAM.RT_READ)
    print('RAM.BALL_WRITE: ', local_RAM.BALL_WRITE)
    print('RAM.BALL_READ: ', local_RAM.BALL_READ)
    print('done!')



# debug_test()
import cProfile
import pstats

with cProfile.Profile() as pr:
    debug_test()

stats = pstats.Stats(pr)
stats.sort_stats(pstats.SortKey.TIME)
# stats.print_stats()
stats.dump_stats(filename='debug_test_local_RAM.prof')