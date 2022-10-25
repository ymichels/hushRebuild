import math
from RAM.ram import RAM
from collections import defaultdict
from utils.byte_operations import ByteOperations
from thresholdGenerator import ThresholdGenerator
from utils.cuckoo_hash import CuckooHash
from utils.helper_functions import get_random_string
from utils.oblivious_sort import ObliviousSort
from config import config

class HashTable:

    def __init__(self, conf:config) -> None:
        self.is_built = False
        self.conf = conf
        self.byte_operations = ByteOperations(conf.MAIN_KEY,conf)
        self.data_ram = RAM(conf.DATA_LOCATION, conf)
        self.bins_ram = RAM(conf.BINS_LOCATION, conf)
        self.overflow_ram = RAM(conf.OVERFLOW_LOCATION, conf)
        self.second_overflow_ram = RAM(conf.OVERFLOW_SECOND_LOCATION, conf)
        self.threshold_generator = ThresholdGenerator(conf)
        self.dummy = b'\x00'*conf.BALL_SIZE
        self.local_stash = {}

    # This function creates random data for testing.
    def createReadMemory(self):
        current_write = 0
        while current_write < self.conf.DATA_SIZE:
            random_bin = [get_random_string(self.conf.BALL_SIZE, self.conf.BALL_STATUS_POSITION, self.conf.DATA_STATUS) for i in range(self.conf.BIN_SIZE)]
            self.data_ram.writeChunks(
                [(current_write, current_write + self.conf.BIN_SIZE_IN_BYTES)], random_bin)
            current_write += self.conf.BIN_SIZE_IN_BYTES
    
    # This function prepares the bins for writing.
    # It fills the bins with empty values.
    def cleanWriteMemory(self):
        # #Cleaning the bins
        current_write = 0
        empty_bin = [self.dummy]*self.conf.BIN_SIZE
        while current_write < self.conf.DATA_SIZE*2:
            self.bins_ram.writeChunks(
                [(current_write, current_write + self.conf.BIN_SIZE_IN_BYTES)], empty_bin)
            current_write += self.conf.BIN_SIZE_IN_BYTES
        
        #Cleaning the overflow pile
        current_write = 0
        FINAL_OVERFLOW_SIZE = 2**math.ceil(math.log(self.conf.OVERFLOW_SIZE + self.conf.LOG_LAMBDA*self.conf.NUMBER_OF_BINS,2))
        while current_write < FINAL_OVERFLOW_SIZE*2:
            self.overflow_ram.writeChunks(
                [(current_write, current_write + self.conf.BIN_SIZE_IN_BYTES)], empty_bin)
            self.second_overflow_ram.writeChunks(
                [(current_write, current_write + self.conf.BIN_SIZE_IN_BYTES)], empty_bin)
            current_write += self.conf.BIN_SIZE_IN_BYTES
        

    def rebuild(self):
        self.ballsIntoBins()
        self.moveSecretLoad()
        self.tightCompaction()
        self.cuckooHashBins()
        self.obliviousBallsIntoBins()
        self.cuckooHashOverflow()
        self.is_built = True
        print('RAM.RT_WRITE: ', RAM.RT_WRITE)
        print('RAM.RT_READ: ', RAM.RT_READ)
        print('RAM.BALL_WRITE: ', RAM.BALL_WRITE)
        print('RAM.BALL_READ: ', RAM.BALL_READ)
        
    def tightCompaction(self):
        offset = self.conf.NUMBER_OF_BINS_IN_OVERFLOW/2
        distance_from_center = 1/2
        midLocation = int(self.conf.EPSILON*self.conf.N)*self.conf.BALL_SIZE
        
        while offset >= 1:
            start_loc = int(midLocation - midLocation*distance_from_center)
            end_loc = midLocation + midLocation*distance_from_center
            self._tightCompaction(start_loc, end_loc, int(offset))
            
            offset /= 2
            distance_from_center /=2
    
    def _tightCompaction(self, startLoc, endLoc, offset):
        for i in range(offset):
            balls = self.byte_operations.readTransposed(self.overflow_ram, offset, startLoc + i*self.conf.BALL_SIZE, 2*self.conf.MU)
            balls = self.localTightCompaction(balls)
            self.byte_operations.writeTransposed(self.overflow_ram, balls, offset, startLoc + i*self.conf.BALL_SIZE)
        
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
        self.threshold_generator.reset()
        current_bin = 0
        iteration_num = 0
        while current_bin < self.conf.NUMBER_OF_BINS:
            #Step 1: read how much each bin is full
            #we can read 1/EPSILON bins at a time since from each bin we read 2*EPSILON*MU balls
            capacity_chunks = [(i*self.conf.BIN_SIZE_IN_BYTES,i*self.conf.BIN_SIZE_IN_BYTES + self.conf.BALL_SIZE) for i in range(current_bin, current_bin + int(1/self.conf.EPSILON))]
            bins_capacity = self.bins_ram.readChunks(capacity_chunks)
            # bins_capacity is a list of int, each int indicates how many balls in the bin
            bins_capacity = [int.from_bytes(bin_capacity, 'big', signed=False) for bin_capacity in bins_capacity]
            
            #Step 2: read the 2*MU*EPSILON top balls from each bin
            chunks = []
            for index,capacity in enumerate(bins_capacity):
                bin_num = index + current_bin
                end_of_bin = bin_num*self.conf.BIN_SIZE_IN_BYTES + self.conf.BALL_SIZE*(capacity+1)
                end_of_bin_minus_epsilon = end_of_bin - int(2*self.conf.MU*self.conf.EPSILON*self.conf.BALL_SIZE)
                chunks.append((end_of_bin_minus_epsilon,end_of_bin))
            balls = self.bins_ram.readChunks(chunks)
            #bin_tops is a list of lists of balls, each list of balls is the top 2*MU*EPSILON from it's bin
            bin_tops = [balls[x:x+int(2*self.conf.MU*self.conf.EPSILON)] for x in range(0, len(balls), int(2*self.conf.MU*self.conf.EPSILON))]
            
            #Step 3: select the secret load and write it to the overflow pile
            self._moveSecretLoad(bins_capacity, bin_tops, iteration_num)
            iteration_num += 1
            current_bin += int(1/self.conf.EPSILON)

    def _moveSecretLoad(self, bins_capacity, bin_tops, iteration_num):
        write_balls = []
        i = 0
        for capacity,bin_top in zip(bins_capacity,bin_tops):
            
            #this is to skip the non-existant bins.
            # Example: 47 bins, epsilon = 1/9.
            # so we pass on 9 bins at a time, but in the last iteration we pass on the last two bins and then we break.
            if iteration_num*(1/self.conf.EPSILON) + i >= self.conf.NUMBER_OF_BINS:
                break
            
            #generate a threshold
            threshold = self.threshold_generator.generate()
            while threshold >= capacity:
                raise Exception("Error, threshold is greator than capacity")
                threshold = self.threshold_generator.regenerate(threshold)
                
            #Add only the balls above the threshold
            write_balls.extend(bin_top[- (capacity - threshold):])
            i +=1
        
        #Add the appropriate amount of dummies
        write_balls.extend([self.dummy]*(2*self.conf.MU - len(write_balls)))
        #Write to the overflow transposed (for the tight compaction later)
        self.byte_operations.writeTransposed(self.overflow_ram, write_balls, self.conf.NUMBER_OF_BINS_IN_OVERFLOW, iteration_num*self.conf.BALL_SIZE)

    def ballsIntoBins(self):
        current_read_pos = 0
        while current_read_pos < self.conf.DATA_SIZE:
            balls = self.data_ram.readChunks(
                [(current_read_pos, current_read_pos + self.conf.LOCAL_MEMORY_SIZE)])
            self._ballsIntoBins(balls)
            current_read_pos += self.conf.LOCAL_MEMORY_SIZE

    def _ballsIntoBins(self, balls):
        local_bins_dict = defaultdict(list)
        for ball in balls:
            local_bins_dict[self.byte_operations.ballToPseudoRandomNumber(
                ball, self.conf.NUMBER_OF_BINS)].append(ball)
        start_locations = [bin_num *
                          self.conf.BIN_SIZE_IN_BYTES for bin_num in local_bins_dict.keys()]
        bins_capacity = zip(local_bins_dict.keys(),
                           self.bins_ram.readBalls(start_locations))
        write_chunks = []
        write_balls = []
        for bin_num, capacity_ball in bins_capacity:
            capacity = int.from_bytes(capacity_ball, 'big', signed=False)
            if capacity >= 2*self.conf.MU -1:
                raise Exception("Error, bin is too full")
            bin_loc = bin_num*self.conf.BIN_SIZE_IN_BYTES
            bin_write_loc = bin_loc + (capacity + 1) * self.conf.BALL_SIZE
            new_balls = local_bins_dict[bin_num]

            # updating the capacity
            new_capacity_ball = (capacity + len(new_balls)
                               ).to_bytes(self.conf.BALL_SIZE, 'big')
            write_chunks.append((bin_loc, bin_loc + self.conf.BALL_SIZE))
            write_balls.append(new_capacity_ball)

            # balls into bin
            write_chunks.append(
                (bin_write_loc, bin_write_loc + len(new_balls)*self.conf.BALL_SIZE))
            write_balls.extend(new_balls)
        self.bins_ram.writeChunks(write_chunks,write_balls)

    def cuckooHashBins(self):
        current_bin_index = 0
        overflow_written = 0
        stashes = []
        while current_bin_index < self.conf.NUMBER_OF_BINS:
            # get the bin
            bin_data = self.bins_ram.readChunks([(current_bin_index*self.conf.BIN_SIZE_IN_BYTES, (current_bin_index +1)*self.conf.BIN_SIZE_IN_BYTES )])
            capacity = int.from_bytes(bin_data[0], 'big', signed=False)
            bin_data = bin_data[1:capacity+1]

            # generate the cuckoo hash
            cuckoo_hash = CuckooHash(self.conf)
            cuckoo_hash.insert_bulk(bin_data)

            # write the data
            hash_tables = cuckoo_hash.table1 + cuckoo_hash.table2
            self.bins_ram.writeChunks([(current_bin_index*self.conf.BIN_SIZE_IN_BYTES, (current_bin_index +1)*self.conf.BIN_SIZE_IN_BYTES )],hash_tables)
            
            # write the stash
            print('stash:', len(cuckoo_hash.stash))
            dummies = [get_random_string(self.conf.BALL_SIZE, self.conf.BALL_STATUS_POSITION,self.conf.STASH_DUMMY_STATUS) for i in range(self.conf.STASH_SIZE - len(cuckoo_hash.stash))]
            stashes += cuckoo_hash.stash + dummies
            if len(stashes) + self.conf.STASH_SIZE >= self.conf.BIN_SIZE:
                stashes = stashes + [self.dummy]*(self.conf.BIN_SIZE - len(stashes))
                self.overflow_ram.writeChunks([(self.conf.OVERFLOW_SIZE + overflow_written*self.conf.BIN_SIZE_IN_BYTES, self.conf.OVERFLOW_SIZE + (overflow_written +1)*self.conf.BIN_SIZE_IN_BYTES )],stashes)
                stashes = []
                overflow_written += 1
            current_bin_index += 1
        self.overflow_ram.writeChunks([(self.conf.OVERFLOW_SIZE + overflow_written*self.conf.BIN_SIZE_IN_BYTES, self.conf.OVERFLOW_SIZE + overflow_written*self.conf.BIN_SIZE_IN_BYTES + len(stashes) )],stashes)
        overflow_written += 1
        #it is of course bad practice to change constants, but since the size of the overflow changes, it was necessary
        self.updateOverflowConfigs(overflow_written)
    
    def updateOverflowConfigs(self, num_of_added_bins):
        self.conf.NUMBER_OF_BINS_IN_OVERFLOW = 2**math.ceil(math.log(self.conf.NUMBER_OF_BINS_IN_OVERFLOW + math.ceil((num_of_added_bins*self.conf.BIN_SIZE)/self.conf.MU),2))
        self.conf.OVERFLOW_SIZE += num_of_added_bins*self.conf.BIN_SIZE
        
    def obliviousBallsIntoBins(self):
        oblivious_sort = ObliviousSort(self.conf)
        self._obliviousBallsIntoBinsFirstIteration(oblivious_sort)
        next_ram = self.overflow_ram
        current_ram = self.second_overflow_ram
        for bit_num in range(1,math.ceil(math.log(self.conf.NUMBER_OF_BINS_IN_OVERFLOW,2))):
            first_bin_index = 0
            for bin_index in range(math.ceil(self.conf.NUMBER_OF_BINS_IN_OVERFLOW/2)):
                first_bin = current_ram.readChunks([(first_bin_index*self.conf.BIN_SIZE_IN_BYTES, (first_bin_index + 1)*self.conf.BIN_SIZE_IN_BYTES)])
                second_bin = current_ram.readChunks([
                    ((first_bin_index + 2**bit_num)*self.conf.BIN_SIZE_IN_BYTES, (first_bin_index + (2**bit_num) + 1)*self.conf.BIN_SIZE_IN_BYTES)])
                bin_zero, bin_one = oblivious_sort.splitToBinsByBit(first_bin + second_bin,math.ceil(math.log(self.conf.NUMBER_OF_BINS_IN_OVERFLOW,2)) - 1 - bit_num, self.conf.NUMBER_OF_BINS_IN_OVERFLOW)
                
                next_ram.writeChunks(
                    [(bin_index*2*self.conf.BIN_SIZE_IN_BYTES, (bin_index +1)*2*self.conf.BIN_SIZE_IN_BYTES)], bin_zero + bin_one)
                first_bin_index +=1
                if first_bin_index % 2**bit_num == 0:
                    first_bin_index += 2**bit_num
            next_ram, current_ram = current_ram, next_ram
        self.overflow_ram = current_ram
        self.second_overflow_ram = next_ram
        print('this is where the real overflow is stored:',self.overflow_ram.fileName)
    
    def _obliviousBallsIntoBinsFirstIteration(self,oblivious_sort):
        current_read_pos = 0
        for bin_index in range(math.ceil(self.conf.NUMBER_OF_BINS_IN_OVERFLOW/2)):
            balls = self.overflow_ram.readChunks([(current_read_pos, current_read_pos + self.conf.BIN_SIZE_IN_BYTES)])
            bin_zero, bin_one = oblivious_sort.splitToBinsByBit(balls, math.ceil(math.log(self.conf.NUMBER_OF_BINS_IN_OVERFLOW,2))-1, self.conf.NUMBER_OF_BINS_IN_OVERFLOW)
            self.second_overflow_ram.writeChunks(
                [(2*current_read_pos, 2*current_read_pos + 2*self.conf.BIN_SIZE_IN_BYTES)], bin_zero + bin_one)
            current_read_pos += self.conf.BIN_SIZE_IN_BYTES
        
    def cuckooHashOverflow(self):
        current_bin_index = 0
        while current_bin_index < self.conf.NUMBER_OF_BINS_IN_OVERFLOW:
            # get the bin
            bin_data = self.overflow_ram.readChunks([(current_bin_index*self.conf.BIN_SIZE_IN_BYTES, (current_bin_index +1)*self.conf.BIN_SIZE_IN_BYTES )])

            # generate the cuckoo hash
            cuckoo_hash = CuckooHash(self.conf)
            cuckoo_hash.insert_bulk(bin_data)

            # write the data
            hash_tables = cuckoo_hash.table1 + cuckoo_hash.table2
            self.overflow_ram.writeChunks([(current_bin_index*self.conf.BIN_SIZE_IN_BYTES, (current_bin_index +1)*self.conf.BIN_SIZE_IN_BYTES )],hash_tables)
            
            # write the stash
            print('stash:', len(cuckoo_hash.stash))
            self.addToLocalStash(cuckoo_hash.stash)
            current_bin_index += 1
    
    def addToLocalStash(self, balls):
        for ball in balls:
            self.local_stash[ball[self.conf.BALL_STATUS_POSITION+1:]] = ball
    
    
    def lookup(self, key):
        # look in local stash
        result_ball = self.dummy
        ball = self.local_stash.get(key)
        if ball != None:
            result_ball = ball
        
        table1_location, table2_location = CuckooHash(self.conf).get_possible_addresses(key)
        
        # look in overflow
        bin_num = self.byte_operations.keyToPseudoRandomNumber(key, self.conf.NUMBER_OF_BINS_IN_OVERFLOW)
        
        # table 1
        ball = self.overflow_ram.readBall(self.conf.BIN_SIZE_IN_BYTES*bin_num + self.conf.BALL_SIZE*table1_location) 
        if ball[self.conf.BALL_STATUS_POSITION+1:] == key:
            result_ball = ball
        
        # table 2
        ball = self.overflow_ram.readBall(self.conf.BIN_SIZE_IN_BYTES*bin_num + self.conf.BALL_SIZE*(self.conf.MU + table2_location)) 
        if ball[self.conf.BALL_STATUS_POSITION+1:] == key:
            result_ball = ball
        
        
        # if the ball was found with a standard data status, then continue with dummy lookups
        if result_ball[self.conf.BALL_STATUS_POSITION] == self.conf.DATA_STATUS:
            key = get_random_string(self.conf.BALL_SIZE - self.conf.BALL_STATUS_POSITION -1)
        
        # look in bins
        bin_num = self.byte_operations.keyToPseudoRandomNumber(key, self.conf.NUMBER_OF_BINS)
        
        # table 1
        ball = self.bins_ram.readBall(self.conf.BIN_SIZE_IN_BYTES*bin_num + self.conf.BALL_SIZE*table1_location) 
        if ball[self.conf.BALL_STATUS_POSITION+1:] == key:
            result_ball =  ball
        
        # table 2
        ball = self.bins_ram.readBall(self.conf.BIN_SIZE_IN_BYTES*bin_num + self.conf.BALL_SIZE*(self.conf.MU + table2_location)) 
        if ball[self.conf.BALL_STATUS_POSITION+1:] == key:
            result_ball =  ball
        
        return result_ball
    