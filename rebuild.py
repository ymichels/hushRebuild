from RAM.ram import RAM
from collections import defaultdict
from byteOperations import ByteOperations
from config import BALL_SIZE, BIN_SIZE, BIN_SIZE_IN_BYTES, BINS_LOCATION, DATA_LOCATION, LOCAL_MEMORY_SIZE, OVERFLOW_LOCATION

class Rebuild:

    def __init__(self, readMemoryLocation) -> None:
        self.byteOperations = ByteOperations()
        self.dataRam = RAM(DATA_LOCATION)
        self.binsRam = RAM(BINS_LOCATION)
        self.overflowRam = RAM(OVERFLOW_LOCATION)
        self.readMemoryStart, self.readMemoryEnd = readMemoryLocation

    def cleanWriteMemory(self):
        currentWrite = 0
        memorySize = self.readMemoryEnd-self.readMemoryStart
        emptyBin = [b'\x00'*BALL_SIZE]*BIN_SIZE
        while currentWrite < memorySize*2:
            self.binsRam.writeChunks(
                [(currentWrite, currentWrite + BIN_SIZE_IN_BYTES)], emptyBin)
            currentWrite += BIN_SIZE_IN_BYTES

    def rebuild(self):
        self.ballsIntoBins()

    def ballsIntoBins(self):
        currentReadPos = self.readMemoryStart
        while currentReadPos < self.readMemoryEnd:
            balls = self.dataRam.readChunks(
                [(currentReadPos, currentReadPos + LOCAL_MEMORY_SIZE)])
            self._ballsIntoBins(balls)
            currentReadPos += LOCAL_MEMORY_SIZE

    def _ballsIntoBins(self, balls):
        localBinsDict = defaultdict(list)
        for ball in balls:
            localBinsDict[self.byteOperations.ballToBinIndex(
                ball)].append(ball)
        startLocations = [binNum *
                          BIN_SIZE_IN_BYTES for binNum in localBinsDict.keys()]
        binsCapacity = zip(localBinsDict.keys(),
                           self.binsRam.readBalls(startLocations))
        writeChunks = []
        writeBalls = []
        for binNum, capacityBall in binsCapacity:
            capacity = int.from_bytes(capacityBall, 'big', signed=False)
            binLoc = binNum*BIN_SIZE_IN_BYTES
            binWriteLoc = binLoc + (capacity + 1) * BALL_SIZE
            newBalls = localBinsDict[binNum]

            # updating the capacity
            newCapacityBall = (capacity + len(newBalls)
                               ).to_bytes(BALL_SIZE, 'big')
            writeChunks.append((binLoc, binLoc + BALL_SIZE))
            writeBalls.append(newCapacityBall)

            # balls into bin
            writeChunks.append(
                (binWriteLoc, binWriteLoc + len(newBalls)*BALL_SIZE))
            writeBalls.extend(newBalls)
        self.binsRam.writeChunks(writeChunks,writeBalls)

