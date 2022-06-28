
from RAM.ram import RAM
from config import BALL_SIZE, BIN_SIZE, BINS_LOCATION, N
from rebuild import Rebuild


Rebuild((0, N*BALL_SIZE)).rebuild()
# binsRam = RAM(BINS_LOCATION)
# print(binsRam.readBall(0+ BALL_SIZE*BIN_SIZE*0))
# print(binsRam.readBall(0+ BALL_SIZE*BIN_SIZE*1))
# print(binsRam.readBall(0+ BALL_SIZE*BIN_SIZE*2))
# print(binsRam.readBall(0+ BALL_SIZE*BIN_SIZE*3))
#https://github.com/ymichels/hushRebuild