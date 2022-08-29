from RAM.ram import RAM
from collections import defaultdict
from utils.byte_operations import ByteOperations
from config import BALL_SIZE, BIN_SIZE, BIN_SIZE_IN_BYTES, BINS_LOCATION, DATA_LOCATION, DATA_SIZE, EPSILON, LOCAL_MEMORY_SIZE, LOG_LAMBDA, MAIN_KEY, MU, N, NUMBER_OF_BINS, OVERFLOW_LOCATION, STASH_SIZE
from thresholdGenerator import ThresholdGenerator
from utils.cuckoo_hash import CuckooHash
from utils.helper_functions import get_random_string

class Rebuild:

    def __init__(self) -> None:
        self.byteOperations = ByteOperations(MAIN_KEY)
        self.dataRam = RAM(DATA_LOCATION)
        self.binsRam = RAM(BINS_LOCATION)
        self.overflowRam = RAM(OVERFLOW_LOCATION)
        self.thresholdGenerator = ThresholdGenerator()
        self.dummy = b'\x00'*BALL_SIZE

    # This function creates random data for testing.
    def createReadMemory(self):
        currentWrite = 0
        while currentWrite < DATA_SIZE:
            # TODO: add data status, not just random
            randomBin = [get_random_string(BALL_SIZE) for i in range(BIN_SIZE)]
            self.dataRam.writeChunks(
                [(currentWrite, currentWrite + BIN_SIZE_IN_BYTES)], randomBin)
            currentWrite += BIN_SIZE_IN_BYTES
    
    # This function prepares the bins for writing.
    # It fills the bins with empty values.
    def cleanWriteMemory(self):
        # #Cleaning the bins
        currentWrite = 0
        emptyBin = [self.dummy]*BIN_SIZE
        while currentWrite < DATA_SIZE*2:
            self.binsRam.writeChunks(
                [(currentWrite, currentWrite + BIN_SIZE_IN_BYTES)], emptyBin)
            currentWrite += BIN_SIZE_IN_BYTES
        
        #Cleaning the overflow pile
        currentWrite = 0
        while currentWrite < EPSILON*DATA_SIZE*2:
            self.overflowRam.writeChunks(
                [(currentWrite, currentWrite + BIN_SIZE_IN_BYTES)], emptyBin)
            currentWrite += BIN_SIZE_IN_BYTES
        

    def rebuild(self):
        self.ballsIntoBins()
        self.moveSecretLoad()
        self.tightCompaction()
        self.cuckooHashBins()
        print('RAM.RT_WRITE: ', RAM.RT_WRITE)
        print('RAM.RT_READ: ', RAM.RT_READ)
        print('RAM.BALL_WRITE: ', RAM.BALL_WRITE)
        print('RAM.BALL_READ: ', RAM.BALL_READ)
        
    def tightCompaction(self):
        offset = int(EPSILON*N/MU)/2
        distanceFromCenter = 1/2
        midLocation = int(EPSILON*N)*BALL_SIZE
        
        while offset >= 1:
            startLoc = int(midLocation - midLocation*distanceFromCenter)
            endLoc = midLocation + midLocation*distanceFromCenter
            self._tightCompaction(startLoc, endLoc, int(offset))
            
            offset /= 2
            distanceFromCenter /=2
    
    def _tightCompaction(self, startLoc, endLoc, offset):
        for i in range(offset):
            balls = self.byteOperations.readTransposed(self.overflowRam, offset, startLoc + i*BALL_SIZE, 2*MU)
            balls = self.localTightCompaction(balls)
            self.byteOperations.writeTransposed(self.overflowRam, balls, offset, startLoc + i*BALL_SIZE)
        
    def localTightCompaction(self, balls):
        dummies = []
        result = []
        for ball in balls:
            if ball == self.dummy:
                dummies.append(ball)
            else:
                result.append(ball)
        result.extend(dummies)
        return result
    
    def moveSecretLoad(self):
        self.thresholdGenerator.reset()
        currentBin = 0
        iterationNum = 0
        while currentBin < NUMBER_OF_BINS:
            #Step 1: read how much each bin is full
            #we can read 1/EPSILON bins at a time since from each bin we read 2*EPSILON*MU balls
            capacityChunks = [(i*BIN_SIZE_IN_BYTES,i*BIN_SIZE_IN_BYTES + BALL_SIZE) for i in range(currentBin, currentBin + int(1/EPSILON))]
            binsCapacity = self.binsRam.readChunks(capacityChunks)
            # binsCapacity is a list of int, each int indicates how many balls in the bin
            binsCapacity = [int.from_bytes(binCapacity, 'big', signed=False) for binCapacity in binsCapacity]
            
            #Step 2: read the 2*MU*EPSILON top balls from each bin
            chunks = []
            for index,capacity in enumerate(binsCapacity):
                binNum = index + currentBin
                endOfBin = binNum*BIN_SIZE_IN_BYTES + BALL_SIZE*(capacity+1)
                endOfBinMinusEpsilon = endOfBin - int(2*MU*EPSILON*BALL_SIZE)
                chunks.append((endOfBinMinusEpsilon,endOfBin))
            balls = self.binsRam.readChunks(chunks)
            #binTops is a list of lists of balls, each list of balls is the top 2*MU*EPSILON from it's bin
            binTops = [balls[x:x+int(2*MU*EPSILON)] for x in range(0, len(balls), int(2*MU*EPSILON))]
            
            #Step 3: select the secret load and write it to the overflow pile
            self._moveSecretLoad(binsCapacity, binTops, iterationNum)
            iterationNum += 1
            currentBin += int(1/EPSILON)

    def _moveSecretLoad(self, binsCapacity, binTops, iterationNum):
        writeBalls = []
        i = 0
        for capacity,binTop in zip(binsCapacity,binTops):
            
            #this is to skip the non-existant bins.
            # Example: 47 bins, epsilon = 1/9.
            # so we pass on 9 bins at a time, but in the last iteration we pass on the last two bins and then we break.
            if iterationNum*(1/EPSILON) + i >= NUMBER_OF_BINS:
                break
            
            #generate a threshold
            threshold = self.thresholdGenerator.generate()
            while threshold >= capacity:
                raise Exception("Error, threshold is greator than capacity")
                threshold = self.thresholdGenerator.regenerate(threshold)
                
            #Add only the balls above the threshold
            writeBalls.extend(binTop[- (capacity - threshold):])
            i +=1
        
        #Add the appropriate amount of dummies
        writeBalls.extend([self.dummy]*(2*MU - len(writeBalls)))
        #Write to the overflow transposed (for the tight compaction later)
        self.byteOperations.writeTransposed(self.overflowRam, writeBalls, int(EPSILON*N/MU), iterationNum*BALL_SIZE)

    def ballsIntoBins(self):
        currentReadPos = 0
        while currentReadPos < DATA_SIZE:
            balls = self.dataRam.readChunks(
                [(currentReadPos, currentReadPos + LOCAL_MEMORY_SIZE)])
            self._ballsIntoBins(balls)
            currentReadPos += LOCAL_MEMORY_SIZE

    def _ballsIntoBins(self, balls):
        localBinsDict = defaultdict(list)
        for ball in balls:
            localBinsDict[self.byteOperations.ballToPseudoRandomNumber(
                ball, NUMBER_OF_BINS)].append(ball)
        startLocations = [binNum *
                          BIN_SIZE_IN_BYTES for binNum in localBinsDict.keys()]
        binsCapacity = zip(localBinsDict.keys(),
                           self.binsRam.readBalls(startLocations))
        writeChunks = []
        writeBalls = []
        for binNum, capacityBall in binsCapacity:
            capacity = int.from_bytes(capacityBall, 'big', signed=False)
            if capacity >= 2*MU -1:
                raise Exception("Error, bin is to full")
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

    def cuckooHashBins(self):
        5+5
        current_bin_index = 0
        iteration_num = 0
        overflow_written = 0
        stashes = []
        while current_bin_index < NUMBER_OF_BINS:
            print(current_bin_index)
            # get the bin
            bin_data = self.binsRam.readChunks([(current_bin_index*BIN_SIZE_IN_BYTES, (current_bin_index +1)*BIN_SIZE_IN_BYTES )])
            capacity = int.from_bytes(bin_data[0], 'big', signed=False)
            bin_data = bin_data[1:capacity+1]

            # generate the cuckoo hash
            cuckoo_hash = CuckooHash()
            cuckoo_hash.insert_bulk(bin_data)

            # write the data
            hash_tables = cuckoo_hash.table1 + cuckoo_hash.table2
            self.binsRam.writeChunks([(current_bin_index*BIN_SIZE_IN_BYTES, (current_bin_index +1)*BIN_SIZE_IN_BYTES )],hash_tables)
            
            # write the stash
            # TODO: add special dummies
            print('stash:', len(cuckoo_hash.stash))
            stashes += cuckoo_hash.stash + [self.dummy]*(STASH_SIZE - len(cuckoo_hash.stash))
            if len(stashes) + STASH_SIZE >= BIN_SIZE:
                stashes = stashes + [self.dummy]*(BIN_SIZE- len(stashes))
                self.overflowRam.writeChunks([(int(DATA_SIZE*EPSILON) + overflow_written*BIN_SIZE_IN_BYTES, int(DATA_SIZE*EPSILON) + (overflow_written +1)*BIN_SIZE_IN_BYTES )],stashes)
                stashes = []
                overflow_written += 1
            current_bin_index += 1
        self.overflowRam.writeChunks([(int(DATA_SIZE*EPSILON) + overflow_written*BIN_SIZE_IN_BYTES, int(DATA_SIZE*EPSILON) + overflow_written*BIN_SIZE_IN_BYTES + len(stashes) )],stashes)
        