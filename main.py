
from RAM.ram import RAM
from config import BALL_SIZE, BIN_SIZE, BINS_LOCATION, N, OVERFLOW_LOCATION
from rebuild import Rebuild


# a = Rebuild()
# a.cleanWriteMemory()
# a.rebuild()

binsRam = RAM(BINS_LOCATION)
# print(binsRam.readBall(0+BALL_SIZE))
print(binsRam.readBall(0+ BALL_SIZE*BIN_SIZE*1 + BALL_SIZE*13))
# print(binsRam.readBall(0+ BALL_SIZE*BIN_SIZE*2))
# print(binsRam.readBall(0+ BALL_SIZE*BIN_SIZE*3))
# print(binsRam.readBall(0+ BALL_SIZE*BIN_SIZE*4))
# print(binsRam.readBall(0+ BALL_SIZE*BIN_SIZE*5))
# print(binsRam.readBall(0+ BALL_SIZE*BIN_SIZE*6))
# print(binsRam.readBall(0+ BALL_SIZE*BIN_SIZE*7))
#https://github.com/ymichels/hushRebuild