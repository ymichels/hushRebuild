
import math
import random
from ORAM import ORAM
from RAM.ram import RAM
from config import config
from hashTable import HashTable
from utils.byte_operations import ByteOperations
from utils.cuckoo_hash import CuckooHash


### ATTENTION - if there are preformance issues, you can replace the *[self.dummy] arrays with something more efficient

# a = ByteOperations(b'Sixteen byte key',config())            
# print(a.constructCapacityThresholdBall(21000,20000))
# print(a.deconstructCapacityThresholdBall(a.constructCapacityThresholdBall(21000,20000)))

conf = config(2**2*config.MU)
a = HashTable(conf)
# a.createReadMemory()
# a.cleanWriteMemory()
a.rebuild(2**2*config.MU)
data_ram = RAM('4/data.txt', a.conf)
for i in range(2**1*config.MU):
    ball_to_read = data_ram.readBall(random.randint(0,2**2*config.MU)*a.conf.BALL_SIZE)
    key = ball_to_read[1 + a.conf.BALL_STATUS_POSITION:]
    a.lookup(key)
    if i % 10_000 == 0:
        print('accesses: ',i)
        print('found ratio: ', a.reals_count)
print(a.reals_count)

#Final test
if False:
    a = ORAM(2**5*config.MU)

    a.cleanWriteMemory()
    # # a.tables[-1].is_built = True
    a.initial_build('testing_data.txt')
    data_ram = RAM('testing_data.txt', a.conf)
    for i in range(2**5*config.MU + 50_000):
        ball_to_read = data_ram.readBall(random.randint(0,2**5*config.MU)*a.conf.BALL_SIZE)
        key = ball_to_read[1 + a.conf.BALL_STATUS_POSITION:]
        a.access('read',key)
        if i % 10_000 == 0:
            print('accesses: ',i)
            print('not-found ratio: ', a.not_found/(i+1))
        
    print('RAM.RT_WRITE: ', RAM.RT_WRITE)
    print('RAM.RT_READ: ', RAM.RT_READ)
    print('RAM.BALL_WRITE: ', RAM.BALL_WRITE)
    print('RAM.BALL_READ: ', RAM.BALL_READ)
    print('done!')
# a.initial_build(a.tables[-1].data_ram.file_path)















# whole_ball = b')Tpb\x01HU_&uv\ts?rb'
# key = b'HU_&uv\ts?rb'

# memory_used = 1_000_000_000_000_000
# memory_stored = ((memory_used/2)/3.5)
# N = memory_stored/100
# MU = 30*(9**3)
# number_of_bins = N/MU
# number_of_bins_in_overflow = (number_of_bins/9) + (number_of_bins*9)/MU
# balls_in_local_storage = number_of_bins_in_overflow*9
# local_memory_size = balls_in_local_storage*100 + MU*2*100
# print('memory_used: ', memory_used)
# print('memory_stored: ', memory_stored)
# print('N: ', N)
# print('local_memory_size: ', local_memory_size)
# print(math.ceil(math.log(8,2)))
# ORAM(2**10*config.MU + 100)
# a = HashTable(conf=config())
# a.cleanWriteMemory()
# a.createReadMemory()
# a.overflow_ram = a.second_overflow_ram
# a.rebuild()
# print(a.lookup(key))
# print('a.conf.NUMBER_OF_BINS_IN_OVERFLOW: ',a.conf.NUMBER_OF_BINS_IN_OVERFLOW)
# a.rebuild()
# print('a.conf.NUMBER_OF_BINS_IN_OVERFLOW: ',a.conf.NUMBER_OF_BINS_IN_OVERFLOW)
# print('STARTING OBLIVIOUS BALLS INTO BINS')
#0 - 000 = 000
#1 - 001 = 001
#2 - 010 = 100
#3 - 2,6  011 = 110,010
#4
#5 - 3  101 = 011
#6 - 6 
#7 - E

# conf= config()
# binsRam = RAM(conf.DATA_LOCATION, conf)
# byte_operations = ByteOperations(conf.MAIN_KEY, conf)
# for i in range(100):
#     ball = binsRam.readBall(conf.BIN_SIZE_IN_BYTES*8 + conf.BALL_SIZE*i) 
#     if ball != b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00':
#         print(ball)
#         bin = byte_operations.ballToPseudoRandomNumber(ball,8)
#         print(bin)


# print(binsRam.readBall(BALL_SIZE*int(BIN_SIZE/512)+ BALL_SIZE*int(BIN_SIZE/2)*(NUMBER_OF_BINS_IN_OVERFLOW)))
# print('RAM.RT_WRITE: ', RAM.RT_WRITE)
# print('RAM.RT_READ: ', RAM.RT_READ)
# print('RAM.BALL_WRITE: ', RAM.BALL_WRITE)
# print('RAM.BALL_READ: ', RAM.BALL_READ)

# a.rebuild()
# RAM(BINS_LOCATION).plusOne()
# RAM(BINS_LOCATION).plusOne()
# RAM(BINS_LOCATION).plusOne()
# binsRam = RAM(BINS_LOCATION)
# print(binsRam.readBall(0+BALL_SIZE))
# print(binsRam.readBall(0+ BALL_SIZE*BIN_SIZE*1 + BALL_SIZE*13))
# print(binsRam.readBall(0+ BALL_SIZE*BIN_SIZE*2))
# print(binsRam.readBall(0+ BALL_SIZE*BIN_SIZE*3))
# print(binsRam.readBall(0+ BALL_SIZE*BIN_SIZE*4))
# print(binsRam.readBall(0+ BALL_SIZE*BIN_SIZE*5))
# print(binsRam.readBall(0+ BALL_SIZE*BIN_SIZE*6))
# print(binsRam.readBall(0+ BALL_SIZE*BIN_SIZE*7))
#https://github.com/ymichels/hushRebuild