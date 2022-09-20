
from RAM.ram import RAM
from config import config
from rebuild import Rebuild
from utils.byte_operations import ByteOperations
from utils.cuckoo_hash import CuckooHash


# a = Rebuild(conf=config())
# print('a.conf.NUMBER_OF_BINS_IN_OVERFLOW: ',a.conf.NUMBER_OF_BINS_IN_OVERFLOW)
# a.rebuild()
# print('a.conf.NUMBER_OF_BINS_IN_OVERFLOW: ',a.conf.NUMBER_OF_BINS_IN_OVERFLOW)
# # a.cleanWriteMemory()
# print('STARTING OBLIVIOUS BALLS INTO BINS')
# a.obliviousBallsIntoBins()
# a.rebuild()
conf= config()
binsRam = RAM(conf.OVERFLOW_SECOND_LOCATION,conf)
byte_operations = ByteOperations(conf.MAIN_KEY, conf)
ball = binsRam.readBall(conf.BIN_SIZE_IN_BYTES*3 + conf.BALL_SIZE*42) 
print(ball)
bin = byte_operations.ballToPseudoRandomNumber(ball,8)
print(bin)
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