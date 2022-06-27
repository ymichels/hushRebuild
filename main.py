
from RAM.ram import RAM
from config import BALL_SIZE, BIN_SIZE, BINS_LOCATION
from rebuild import Rebuild


#Rebuild((0, STATIC_MEMORY_END_POSITION)).ballsIntoBins()
binsRam = RAM(BINS_LOCATION)
print(binsRam.readBall(0+ BALL_SIZE*BIN_SIZE*3))
#https://github.com/ymichels/hushRebuild