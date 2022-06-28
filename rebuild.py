from RAM.ram import RAM
from collections import defaultdict
from byteOperations import ByteOperations
from config import BALL_SIZE, BIN_SIZE, BIN_SIZE_IN_BYTES, BINS_LOCATION, DATA_LOCATION, EPSILON, LOCAL_MEMORY_SIZE, MU, NUMBER_OF_BINS, OVERFLOW_LOCATION
from thresholdGenerator import ThresholdGenerator

class Rebuild:

    def __init__(self, readMemoryLocation) -> None:
        self.byteOperations = ByteOperations()
        self.dataRam = RAM(DATA_LOCATION)
        self.binsRam = RAM(BINS_LOCATION)
        self.overflowRam = RAM(OVERFLOW_LOCATION)
        self.readMemoryStart, self.readMemoryEnd = readMemoryLocation
        self.thresholdGenerator = ThresholdGenerator()

    # This function prepares the bins for writing.
    # It fills the bins with empty values.
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
        self.moveSecretLoad()
        
    def moveSecretLoad(self):
        self.thresholdGenerator.reset()
        currentBin = 0
        while currentBin < NUMBER_OF_BINS:
            #Step 1: read how much each bin is full
            #we can read 1/EPSILON bins at a time since from each bin we read EPSILON*MU balls
            capacityChunks = [(i*BIN_SIZE_IN_BYTES,i*BIN_SIZE_IN_BYTES + BALL_SIZE) for i in range(currentBin, currentBin + int(1/EPSILON))]
            binsCapacity = self.binsRam.readChunks(capacityChunks)
            # binsCapacity is a list of int, each int indicates how many balls in the bin
            binsCapacity = [int.from_bytes(binCapacity, 'big', signed=False) for binCapacity in binsCapacity]
            
            #Step 2: read the MU*EPSILON top balls from each bin
            chunks = []
            for index,capacity in enumerate(binsCapacity):
                binNum = index + currentBin
                endOfBin = binNum*BIN_SIZE_IN_BYTES + BALL_SIZE*(capacity+1)
                endOfBinMinusEpsilon = endOfBin - int(MU*EPSILON*BALL_SIZE)
                chunks.append((endOfBinMinusEpsilon,endOfBin))
            balls = self.binsRam.readChunks(chunks)
            #binTops is a list of lists of balls, each list of balls is the top MU*EPSILON from it's bin
            binTops = [balls[x:x+int(MU*EPSILON)] for x in range(0, len(balls), int(MU*EPSILON))]
            
            #Step 3: select the secret load and write it to the overflow pile
            self._moveSecretLoad(binsCapacity,binTops)
            currentBin += int(1/EPSILON)

    def _moveSecretLoad(self, binsCapacity,binTops):
        writeBalls = []
        for capacity,binTop in zip(binsCapacity,binTops):
            #Add only the balls above the threshold
            threshold = self.thresholdGenerator.generate()
            writeBalls.extend(binTop[- (capacity - threshold):])
        
        #Add the appropriate amount of dummies
        writeBalls.extend([b'\x00'*BALL_SIZE]*(MU - len(writeBalls)))
        #Write to the end of the overflow
        self.overflowRam.appendBalls(writeBalls)

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

