
import random
from ORAM import ORAM
from PathORAM.path_ORAM import PathORAM
from RAM.local_RAM import local_RAM, reset_counters
from RAM.file_RAM import file_RAM
from config import config
from utils.helper_functions import get_random_string

#https://github.com/ymichels/hushRebuild

# path ORAM test
def path_ORAM_test(number_of_blocks):

    # real_ram = {}
    path_oram = PathORAM(number_of_blocks,True)
    # allocating memory shouldn't count as 'writing'...
    reset_counters()
    for i in range(number_of_blocks):
        data = b'\x16'*path_oram.conf.BALL_DATA_SIZE
        # real_ram[i] = data
        path_oram.access('write',i,data)
        if i % 1_000 == 0:
            print(i,': ',len(path_oram.local_stash))

    for i in range(number_of_blocks):
        if i % 1_000 == 0:
            print(i,': ',len(path_oram.local_stash))
        key = random.randint(0,number_of_blocks - 1)
        oram_ans = path_oram.access('read', key)
        # if oram_ans != real_ram[key]:
        #     raise 'ERROR!'
    
    print('RAM.RT_WRITE: ', local_RAM.RT_WRITE)
    print('RAM.RT_READ: ', local_RAM.RT_READ)
    print('RAM.BALL_WRITE: ', local_RAM.BALL_WRITE)
    print('RAM.BALL_READ: ', local_RAM.BALL_READ)
    print('done!')
    
    
    
#our ORAM test
def our_ORAM_test(oram_size):
    oram = ORAM(oram_size)
    oram.cleanWriteMemory()

    # allocating memory shouldn't count as 'writing'...
    reset_counters()
    oram.initial_build('testing_data.txt')
    for i in range(oram_size*2-1):
        read_ball = oram.access('read',random.randint(0,oram_size-1).to_bytes(oram.conf.KEY_SIZE,'big'))
        if i % 10_000 == 0:
            print('accesses: ',i)
    
    print('RAM.RT_WRITE: ', local_RAM.RT_WRITE)
    print('RAM.RT_READ: ', local_RAM.RT_READ)
    print('RAM.BALL_WRITE: ', local_RAM.BALL_WRITE)
    print('RAM.BALL_READ: ', local_RAM.BALL_READ)
    print('done!')

def ram_test(number_of_blocks):
    ram = local_RAM('bla',config(number_of_blocks))
    ram.generate_random_memory(number_of_blocks)
    reset_counters()
    print('generated')
    for i in range(number_of_blocks*2):
        ball = ram.readBall(random.randint(0,number_of_blocks-1)*ram.conf.BALL_SIZE)
        ram.writeBall(random.randint(0,number_of_blocks-1)*ram.conf.BALL_SIZE,ball)
        if i % 10_000 == 0:
            print('accesses: ',i)
    print('RAM.RT_WRITE: ', local_RAM.RT_WRITE)
    print('RAM.RT_READ: ', local_RAM.RT_READ)
    print('RAM.BALL_WRITE: ', local_RAM.BALL_WRITE)
    print('RAM.BALL_READ: ', local_RAM.BALL_READ)
    print('done!')



import cProfile
import pstats


test_type = int(input('Enter test type:\n1) Our ORAM\n2) Path ORAM\n3) RAM\n'))
number_of_MB = int(input('How many MB should the test run?\n'))
number_of_blocks = int((number_of_MB*(2**20))/16)
with cProfile.Profile() as pr:
    if test_type == 1:
        our_ORAM_test(number_of_blocks)
    elif test_type == 2:
        path_ORAM_test(number_of_blocks)
    else:
        ram_test(number_of_blocks)

stats = pstats.Stats(pr)
stats.sort_stats(pstats.SortKey.TIME)
stats.dump_stats(filename='test-{}.size-{}MB.prof'.format(test_type, number_of_MB))

file = open('test-{}.size-{}MB'.format(test_type, number_of_MB),'w')
file.write(
    'accesses:{}\n'.format(number_of_blocks*2) +
    'RAM.RT_WRITE:{}\n'.format(local_RAM.RT_WRITE) +
    'RAM.RT_READ:{}\n'.format(local_RAM.RT_READ) +
    'RAM.BALL_WRITE:{}\n'.format(local_RAM.BALL_WRITE) +
    'RAM.BALL_READ:{}\n'.format(local_RAM.BALL_READ)
)


file.close()


