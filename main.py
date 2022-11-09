
import random
from ORAM import ORAM
from RAM.ram import RAM
from config import config

#https://github.com/ymichels/hushRebuild


#TODO read/write test

#Final test
if False:
    oram_size = 2**4*config.MU
    oram = ORAM(oram_size)
    oram.cleanWriteMemory()
    oram.initial_build('testing_data.txt')
    data_ram = RAM('testing_data.txt', oram.conf)
    for i in range(oram_size + 50_000):
        ball_to_read = data_ram.readBall(random.randint(0,oram_size-1)*oram.conf.BALL_SIZE)
        key = ball_to_read[1 + oram.conf.BALL_STATUS_POSITION:]
        oram.access('read',key)
        if i % 10_000 == 0:
            print('accesses: ',i)
        
    print('RAM.RT_WRITE: ', RAM.RT_WRITE)
    print('RAM.RT_READ: ', RAM.RT_READ)
    print('RAM.BALL_WRITE: ', RAM.BALL_WRITE)
    print('RAM.BALL_READ: ', RAM.BALL_READ)
    print('done!')
    
    
    
#Debug test
if True:
    oram_size = 2**3*config.MU
    oram = ORAM(oram_size)
    oram.cleanWriteMemory()
    oram.initial_build('testing_data.txt')
    data_ram = RAM('testing_data.txt', oram.conf)
    o = 0
    j=0
    for i in range(oram_size + 50_000):
        ball_to_read = data_ram.readBall(random.randint(0,oram_size-1)*oram.conf.BALL_SIZE)
        key = ball_to_read[1 + oram.conf.BALL_STATUS_POSITION:]
        oram.access('read',key)
        j+=1
        if o != oram.not_found:
            o= oram.not_found
            j=0
        if i % 10_000 == 0:
            print('accesses: ',i)
            print('not-found ratio: ', oram.not_found/(i+1))
        
    print('RAM.RT_WRITE: ', RAM.RT_WRITE)
    print('RAM.RT_READ: ', RAM.RT_READ)
    print('RAM.BALL_WRITE: ', RAM.BALL_WRITE)
    print('RAM.BALL_READ: ', RAM.BALL_READ)
    print('done!')
