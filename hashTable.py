import math
from RAM.local_RAM import local_RAM
from collections import defaultdict
from utils.byte_operations import ByteOperations
from thresholdGenerator import ThresholdGenerator
from utils.cuckoo_hash import CuckooHash
from utils.helper_functions import get_random_string
from utils.oblivious_sort import ObliviousSort
from config import config
from operator import itemgetter
import random

class HashTable:

    def __init__(self, conf:config) -> None:
        self.is_built = False
        self.conf = conf
        self.byte_operations = ByteOperations(conf.MAIN_KEY,conf)
        self.data_ram = local_RAM(conf.DATA_LOCATION, conf)
        self.bins_ram = local_RAM(conf.BINS_LOCATION, conf)
        self.overflow_ram = local_RAM(conf.OVERFLOW_LOCATION, conf)
        self.second_overflow_ram = local_RAM(conf.OVERFLOW_SECOND_LOCATION, conf)
        self.threshold_generator = ThresholdGenerator(conf)
        self.local_stash = {}
        self.mixed_stripe_ram = local_RAM(conf.MIXED_STRIPE_LOCATION, conf)
        self.cuckoo = CuckooHash(conf)
        self.dummy = conf.DUMMY_STATUS*conf.BALL_SIZE
        self.dummy_bin = self.createDummies(conf.BIN_SIZE)
        
        

    def createDummies(self, count):
        return [self.dummy]*count
    
    # This function creates random data for testing.
    def createReadMemory(self):
        current_write = 0
        while current_write < self.conf.DATA_SIZE:
            random_bin = [get_random_string(self.conf.BALL_SIZE, self.conf.BALL_STATUS_POSITION, self.conf.DATA_STATUS) for i in range(self.conf.BIN_SIZE)]
            self.data_ram.writeChunks(
                [(current_write, current_write + self.conf.BIN_SIZE_IN_BYTES)], random_bin)
            current_write += self.conf.BIN_SIZE_IN_BYTES
        while current_write < 2*self.conf.DATA_SIZE:
            self.data_ram.writeChunks(
                [(current_write, current_write + self.conf.BIN_SIZE_IN_BYTES)], self.createDummies(self.conf.BIN_SIZE))
            current_write += self.conf.BIN_SIZE_IN_BYTES
    
    # This function prepares the bins for writing.
    # It fills the bins with empty values.
    def cleanWriteMemory(self):
        # Cleaning the bins
        current_write = 0
        while current_write < self.conf.DATA_SIZE*2:
            self.bins_ram.writeChunks(
                [(current_write, current_write + self.conf.BIN_SIZE_IN_BYTES)], self.createDummies(self.conf.BIN_SIZE))
            current_write += self.conf.BIN_SIZE_IN_BYTES
        
        #Cleaning the overflow pile
        current_write = 0
        FINAL_OVERFLOW_SIZE = 2**math.ceil(math.log(self.conf.OVERFLOW_SIZE + self.conf.LOG_LAMBDA*self.conf.NUMBER_OF_BINS,2))
        while current_write < FINAL_OVERFLOW_SIZE*2:
            self.overflow_ram.writeChunks(
                [(current_write, current_write + self.conf.BIN_SIZE_IN_BYTES)], self.createDummies(self.conf.BIN_SIZE))
            self.second_overflow_ram.writeChunks(
                [(current_write, current_write + self.conf.BIN_SIZE_IN_BYTES)], self.createDummies(self.conf.BIN_SIZE))
            current_write += self.conf.BIN_SIZE_IN_BYTES
    
    def emptyData(self):
        current_write = 0
        while current_write < 2*self.conf.DATA_SIZE:
            self.data_ram.writeChunks(
                [(current_write, current_write + self.conf.BIN_SIZE_IN_BYTES)], self.createDummies(self.conf.BIN_SIZE))
            current_write += self.conf.BIN_SIZE_IN_BYTES
        

    def rebuild(self, reals):
        self.reals_count = reals
        self.local_stash = {}
        self.ballsIntoBins()
        self.moveSecretLoad()
        self.tightCompaction(self.conf.NUMBER_OF_BINS_IN_OVERFLOW, self.overflow_ram)
        self.cuckooHashBins()
        self.obliviousBallsIntoBins()
        self.cuckooHashOverflow()
        self.is_built = True
        print('rebuilt layer: ', self.bins_ram.file_path)
        
    def binsTightCompaction(self, dummy_statuses = None):
        self.tightCompaction(self.conf.NUMBER_OF_BINS, self.bins_ram, dummy_statuses)
        
    def tightCompaction(self, NUMBER_OF_BINS, ram, dummy_statuses = None):
        if dummy_statuses == None:
            dummy_statuses = [self.conf.DUMMY_STATUS]
        offset = NUMBER_OF_BINS
        distance_from_center = 1
        midLocation = int(self.conf.EPSILON*self.conf.N)*self.conf.BALL_SIZE
        
        while offset >= 1:
            start_loc = int(midLocation - midLocation*distance_from_center)
            self._tightCompaction(start_loc, ram, int(offset), dummy_statuses)
            
            offset /= 2
            distance_from_center /=2
    
    def _tightCompaction(self, start_loc, ram, offset, dummy_statuses):
        for i in range(offset):
            balls = self.byte_operations.readTransposed(ram, offset, start_loc + i*self.conf.BALL_SIZE, 2*self.conf.MU)
            balls = self.localTightCompaction(balls, dummy_statuses)
            self.byte_operations.writeTransposed(ram, balls, offset, start_loc + i*self.conf.BALL_SIZE)
        
    def localTightCompaction(self, balls, dummy_statuses):
        dummies = []
        result = []
        for ball in balls:
            if ball[self.conf.BALL_STATUS_POSITION: self.conf.BALL_STATUS_POSITION + 1 ] in dummy_statuses:
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
            # Step 1: read how much each bin is full
            # we can read 1/EPSILON bins at a time since from each bin we read 2*EPSILON*MU balls
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
            # bin_tops is a list of lists of balls, each list of balls is the top 2*MU*EPSILON from it's bin
            bin_tops = [balls[x:x+int(2*self.conf.MU*self.conf.EPSILON)] for x in range(0, len(balls), int(2*self.conf.MU*self.conf.EPSILON))]
            
            # Step 3: select the secret load and write it to the overflow pile (also update the capacities)
            capacity_threshold_balls = self._moveSecretLoad(bins_capacity, bin_tops, iteration_num, chunks)
            iteration_num += 1
            current_bin += int(1/self.conf.EPSILON)
            
            self.bins_ram.writeChunks(capacity_chunks[:len(capacity_threshold_balls)], capacity_threshold_balls)

    def _moveSecretLoad(self, bins_capacity, bin_tops, iteration_num, write_to_bins_chunks):
        write_balls = []
        write_back_balls = []
        i = 0
        capacity_threshold_balls = []
        for capacity,bin_top in zip(bins_capacity,bin_tops):
            
            # This is to skip the non-existant bins.
            # Example: 32 bins, epsilon = 1/9.
            # so we pass on 9 bins at a time, but in the last iteration we pass on the last five bins and then we break.
            if iteration_num*(1/self.conf.EPSILON) + i >= self.conf.NUMBER_OF_BINS:
                break
            
            # generate a threshold
            threshold = self.threshold_generator.generate()
            while threshold >= capacity:
                raise Exception("Error, threshold is greater than capacity")
                
            # Add only the balls above the threshold
            write_balls.extend(bin_top[- (capacity - threshold):])
            i +=1
            
            # write back only the balls beneath the threshold
            write_back = bin_top[:- (capacity - threshold)]
            write_back.extend(self.createDummies(len(bin_top) - len(write_back)))
            write_back_balls.extend(write_back)
            
            
            capacity_threshold_balls.append(self.byte_operations.constructCapacityThresholdBall(capacity, threshold))
        
        # Add the appropriate amount of dummies
        write_balls.extend(self.createDummies(2*self.conf.MU - len(write_balls)))
        
        # Write to the overflow transposed (for the tight compaction later)
        self.byte_operations.writeTransposed(self.overflow_ram, write_balls, self.conf.NUMBER_OF_BINS_IN_OVERFLOW, iteration_num*self.conf.BALL_SIZE)
        
        # Write back to the bins
        self.bins_ram.writeChunks(write_to_bins_chunks[:i], write_back_balls)
        
        return capacity_threshold_balls

    def ballsIntoBins(self):
        current_read_pos = 0
        balls = []
        
        # in the final table to save space, the rams switch.
        if self.conf.FINAL:
            self.data_ram, self.bins_ram = self.bins_ram, self.data_ram
        
        while current_read_pos < self.bins_ram.getSize():
            balls = self.data_ram.readChunks(
                [(current_read_pos, current_read_pos + self.conf.LOCAL_MEMORY_SIZE)])
            
            # this is to get rid of SECOND_DATA_STATUS from the intersperse stage
            balls = self.byte_operations.removeSecondStatus(balls)
            
            self._ballsIntoBins(balls)
            current_read_pos += self.conf.LOCAL_MEMORY_SIZE
        
        
        self.conf.reset()
        
            
            

    def _ballsIntoBins(self, balls):
        local_bins_dict = defaultdict(list)
        for ball in balls:
            if ball[self.conf.BALL_STATUS_POSITION: self.conf.BALL_STATUS_POSITION + 1] == self.conf.DUMMY_STATUS:
                local_bins_dict[int(random.randint(0,self.conf.NUMBER_OF_BINS-1))].append(self.dummy)
            else:
                local_bins_dict[self.byte_operations.ballToPseudoRandomNumber(ball, self.conf.NUMBER_OF_BINS)].append(ball)
        
        start_locations = [bin_num * self.conf.BIN_SIZE_IN_BYTES for bin_num in local_bins_dict.keys()]
        bins_capacity = zip(local_bins_dict.keys(), self.bins_ram.readBalls(start_locations))
        
        write_chunks = []
        write_balls = []
        for bin_num, capacity_ball in bins_capacity:
            capacity = self.byte_operations.getCapacity(capacity_ball)
            if capacity >= 2*self.conf.MU -1:
                raise Exception("Error, bin is too full")
            bin_loc = bin_num*self.conf.BIN_SIZE_IN_BYTES
            bin_write_loc = bin_loc + (capacity + 1) * self.conf.BALL_SIZE
            new_balls = local_bins_dict[bin_num]

            # updating the capacity
            new_capacity_ball = (capacity + len(new_balls)).to_bytes(self.conf.BALL_SIZE, 'big')
            write_chunks.append((bin_loc, bin_loc + self.conf.BALL_SIZE))
            write_balls.append(new_capacity_ball)

            # balls into bin
            write_chunks.append((bin_write_loc, bin_write_loc + len(new_balls) * self.conf.BALL_SIZE))
            write_balls.extend(new_balls)
        self.bins_ram.writeChunks(write_chunks,write_balls)

    def cuckooHashBins(self):
        current_bin_index = 0
        overflow_written = 0
        stashes = []
        while current_bin_index < self.conf.NUMBER_OF_BINS:
            
            # get the bin
            bin_data = self.bins_ram.readChunks([(current_bin_index*self.conf.BIN_SIZE_IN_BYTES, (current_bin_index +1)*self.conf.BIN_SIZE_IN_BYTES )])
            capacity, threshold = self.byte_operations.deconstructCapacityThresholdBall(bin_data[0])
            bin_data = bin_data[1:threshold+1]
            
            # generate the cuckoo hash
            cuckoo_hash = CuckooHash(self.conf)
            cuckoo_hash.insert_bulk(bin_data)

            # write the data
            hash_tables = cuckoo_hash.table1 + cuckoo_hash.table2
            self.bins_ram.writeChunks([(current_bin_index*self.conf.BIN_SIZE_IN_BYTES, (current_bin_index +1)*self.conf.BIN_SIZE_IN_BYTES )],hash_tables)
            
            # write the stash
            dummies = [get_random_string(self.conf.BALL_SIZE, self.conf.BALL_STATUS_POSITION,self.conf.STASH_DUMMY_STATUS) for i in range(self.conf.STASH_SIZE - len(cuckoo_hash.stash))]
            stashes += cuckoo_hash.stash + dummies
            if len(stashes) + self.conf.STASH_SIZE >= self.conf.BIN_SIZE:
                stashes = stashes + self.createDummies(self.conf.BIN_SIZE - len(stashes))
                self.overflow_ram.writeChunks([(self.conf.OVERFLOW_SIZE + overflow_written*self.conf.BIN_SIZE_IN_BYTES, self.conf.OVERFLOW_SIZE + (overflow_written +1)*self.conf.BIN_SIZE_IN_BYTES )],stashes)
                stashes = []
                overflow_written += 1
            current_bin_index += 1
        self.overflow_ram.writeChunks([(self.conf.OVERFLOW_SIZE + overflow_written*self.conf.BIN_SIZE_IN_BYTES, self.conf.OVERFLOW_SIZE + overflow_written*self.conf.BIN_SIZE_IN_BYTES + len(stashes) )],stashes)
        overflow_written += 1
        
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
            self.addToLocalStash(cuckoo_hash.stash)
            current_bin_index += 1
    
    def addToLocalStash(self, balls):
        for ball in balls:
            self.local_stash[ball[self.conf.BALL_STATUS_POSITION+1:]] = ball
       
    def lookup(self, key):
        # look in local stash
        result_ball = self.createDummies(1)[0]
        ball = self.local_stash.get(key)
        if ball != None:
            result_ball = ball
            del self.local_stash[key]
            self.reals_count -= 1
        
        table1_location, table2_location = self.cuckoo.get_possible_addresses(key)
        
        # look in overflow
        bin_num = self.byte_operations.keyToPseudoRandomNumber(key, self.conf.NUMBER_OF_BINS_IN_OVERFLOW)
        replacement_ball = self.createDummies(1)[0]
        
        # read
        ball_1,ball_2 = self.overflow_ram.readBalls([self.conf.BIN_SIZE_IN_BYTES*bin_num + self.conf.BALL_SIZE*table1_location,self.conf.BIN_SIZE_IN_BYTES*bin_num + self.conf.BALL_SIZE*(self.conf.MU + table2_location)]) 
        ball_1_write = ''
        ball_2_write = ''
        # table 1
        if ball_1[self.conf.BALL_STATUS_POSITION+1:] == key:
            result_ball = ball_1
            ball_1_write = replacement_ball
            self.reals_count -= 1
        else:
            ball_1_write = ball_1
        
        # table 2
        if ball_2[self.conf.BALL_STATUS_POSITION+1:] == key:
            result_ball = ball_2
            ball_2_write = replacement_ball
            self.reals_count -= 1
        else:
            ball_2_write = ball_2
        
        self.overflow_ram.writeBalls([self.conf.BIN_SIZE_IN_BYTES*bin_num + self.conf.BALL_SIZE*table1_location, self.conf.BIN_SIZE_IN_BYTES*bin_num + self.conf.BALL_SIZE*(self.conf.MU + table2_location)], [ball_1_write, ball_2_write])

        # if the ball was found with a standard data status, then continue with dummy lookups
        if result_ball[self.conf.BALL_STATUS_POSITION: self.conf.BALL_STATUS_POSITION + 1] == self.conf.DATA_STATUS:
            key = get_random_string(self.conf.BALL_SIZE - self.conf.BALL_STATUS_POSITION -1)
        
        # look in bins
        bin_num = self.byte_operations.keyToPseudoRandomNumber(key, self.conf.NUMBER_OF_BINS)
        
        ball_1,ball_2 = self.bins_ram.readBalls([self.conf.BIN_SIZE_IN_BYTES*bin_num + self.conf.BALL_SIZE*table1_location, self.conf.BIN_SIZE_IN_BYTES*bin_num + self.conf.BALL_SIZE*(self.conf.MU + table2_location)]) 


        # table 1
        if ball_1[self.conf.BALL_STATUS_POSITION+1:] == key:
            result_ball = ball_1
            ball_1_write = replacement_ball
            self.reals_count -= 1
        else:
            ball_1_write = ball_1
        
        # table 2
        if ball_2[self.conf.BALL_STATUS_POSITION+1:] == key:
            result_ball = ball_2
            ball_2_write = replacement_ball
            self.reals_count -= 1
        else:
            ball_2_write = ball_2
        self.bins_ram.writeBalls([self.conf.BIN_SIZE_IN_BYTES*bin_num + self.conf.BALL_SIZE*table1_location, self.conf.BIN_SIZE_IN_BYTES*bin_num + self.conf.BALL_SIZE*(self.conf.MU + table2_location)], [ball_1_write, ball_2_write])

        return result_ball

    # this function copies the previous layer into the current layer for intersperse
    def copyToEndOfBins(self, second_data_ram:local_RAM, reals):
        current_read_pos = 0
        self.reals_count += reals
        while current_read_pos < self.conf.DATA_SIZE:
            balls = second_data_ram.readChunks(
                [(current_read_pos, current_read_pos + self.conf.LOCAL_MEMORY_SIZE)])
            balls = self.byte_operations.removeSecondStatus(balls)
            self.bins_ram.writeChunks(
                [(self.conf.DATA_SIZE + current_read_pos, self.conf.DATA_SIZE + current_read_pos + self.conf.LOCAL_MEMORY_SIZE)], balls)
            current_read_pos += self.conf.LOCAL_MEMORY_SIZE
    
    
    
    def extract(self):
        self.tightCompactionHideMixedStripe()
        self.intersperseRD()
    
    def tightCompactionHideMixedStripe(self):
        
        # individual case of one bin
        if self.conf.NUMBER_OF_BINS == 1:
            balls = self.bins_ram.readChunks([(0,self.conf.BIN_SIZE_IN_BYTES)])
            balls = self.localTightCompaction(balls, [self.conf.DUMMY_STATUS])
            stash_balls = list(self.local_stash.values())
            balls = balls[:self.conf.MU-len(stash_balls)] + stash_balls
            self.bins_ram.writeChunks([(0,self.conf.MU * self.conf.BALL_SIZE)], balls)
            return
        
        self.copyOverflowToBins()
        
        number_of_bins = self.conf.NUMBER_OF_BINS + self.conf.NUMBER_OF_BINS_IN_OVERFLOW
        mixed_stripe_write = 0
        mixed_stripe_start, mixed_stripe_end = self.getMixedStripeLocation()
        
        for i in range(number_of_bins):
            balls, mixed_indexes = self.byte_operations.readTransposedGetMixedStripeIndexes(self.bins_ram, number_of_bins, i*self.conf.BALL_SIZE, 2*self.conf.MU, mixed_stripe_start, mixed_stripe_end)
            balls = self.localTightCompaction(balls, [self.conf.DUMMY_STATUS])
            mixed_stripe = list(itemgetter(*mixed_indexes)(balls))
            self.mixed_stripe_ram.writeChunks([(mixed_stripe_write, mixed_stripe_write + len(mixed_stripe)*self.conf.BALL_SIZE)],mixed_stripe)
            mixed_stripe_write += len(mixed_stripe)*self.conf.BALL_SIZE
            self.byte_operations.writeTransposed(self.bins_ram, balls, number_of_bins, i*self.conf.BALL_SIZE)
        
        self.tightCompaction(int(self.conf.NUMBER_OF_BINS/2), self.mixed_stripe_ram)
        self.byte_operations.obliviousShiftData(self.mixed_stripe_ram, int(self.conf.NUMBER_OF_BINS/2), mixed_stripe_start)
        
        current_write = 0
        while current_write < self.conf.DATA_SIZE*2:
            stripe_balls = self.mixed_stripe_ram.readChunks([(current_write % (self.conf.N*self.conf.BALL_SIZE), (current_write % (self.conf.N*self.conf.BALL_SIZE)) + self.conf.BIN_SIZE_IN_BYTES)])
            bins_balls = self.bins_ram.readChunks([(current_write, current_write + self.conf.BIN_SIZE_IN_BYTES)])
            if current_write > mixed_stripe_end or current_write + self.conf.BIN_SIZE_IN_BYTES < mixed_stripe_start:
                self.bins_ram.writeChunks([(current_write, current_write + self.conf.BIN_SIZE_IN_BYTES)],bins_balls)
            elif current_write >= mixed_stripe_start and current_write + self.conf.BIN_SIZE_IN_BYTES <= mixed_stripe_end:
                self.bins_ram.writeChunks([(current_write, current_write + self.conf.BIN_SIZE_IN_BYTES)], stripe_balls)
            elif current_write < mixed_stripe_start and current_write + self.conf.BIN_SIZE_IN_BYTES >= mixed_stripe_start:
                edge_balls = bins_balls[:int((mixed_stripe_start - current_write)/self.conf.BALL_SIZE)] + stripe_balls[int((mixed_stripe_start - current_write)/self.conf.BALL_SIZE):]
                self.bins_ram.writeChunks([(current_write, current_write + self.conf.BIN_SIZE_IN_BYTES)], edge_balls)
            elif current_write >= mixed_stripe_start and current_write + self.conf.BIN_SIZE_IN_BYTES >= mixed_stripe_end:
                edge_balls = stripe_balls[:int((mixed_stripe_start - current_write)/self.conf.BALL_SIZE)] + bins_balls[int((mixed_stripe_start - current_write)/self.conf.BALL_SIZE):]
                self.bins_ram.writeChunks([(current_write, current_write + self.conf.BIN_SIZE_IN_BYTES)], edge_balls)
            current_write += self.conf.BIN_SIZE_IN_BYTES
        
       
    def getMixedStripeLocation(self):
        if self.reals_count < self.conf.N/2:
            return 0, self.conf.N*self.conf.BALL_SIZE
        return int((self.reals_count - self.conf.N/2)*self.conf.BALL_SIZE), int((self.reals_count + self.conf.N/2)*self.conf.BALL_SIZE)
        
    def copyOverflowToBins(self):
        current_read_pos = 0
        
        while current_read_pos < self.conf.NUMBER_OF_BINS_IN_OVERFLOW*self.conf.BIN_SIZE_IN_BYTES:
            balls = self.overflow_ram.readChunks(
                [(current_read_pos, current_read_pos + self.conf.LOCAL_MEMORY_SIZE)])
            self.overflow_ram.writeChunks([(current_read_pos, current_read_pos + self.conf.LOCAL_MEMORY_SIZE)],self.dummy_bin)
            self.reset_overflow_statuses(balls)
            self.bins_ram.writeChunks(
                [(self.conf.DATA_SIZE*2 + current_read_pos, self.conf.DATA_SIZE*2 + current_read_pos + self.conf.LOCAL_MEMORY_SIZE)], balls)
            current_read_pos += self.conf.LOCAL_MEMORY_SIZE
    
    
    def reset_overflow_statuses(self, balls):
        stash_inserted = 0
        for i,ball in enumerate(balls):
            status = ball[self.conf.BALL_STATUS_POSITION: self.conf.BALL_STATUS_POSITION + 1] 
            if status == self.conf.STASH_DATA_STATUS:
                balls[i] = self.byte_operations.changeBallStatus(ball, self.conf.DATA_STATUS)
            elif status == self.conf.STASH_DUMMY_STATUS:
                balls[i] = self.byte_operations.changeBallStatus(ball, self.conf.DUMMY_STATUS)
            if status == self.conf.DUMMY_STATUS and stash_inserted < self.conf.STASH_SIZE and len(self.local_stash) != 0:
                balls[i] = list(self.local_stash.items())[0][1]
                del self.local_stash[list(self.local_stash.items())[0][0]]
        
    
    def intersperse(self):
        self.markAuxiliary(self.conf.N, 2*self.conf.N)
        self.binsTightCompaction([self.conf.SECOND_DATA_STATUS, self.conf.SECOND_DUMMY_STATUS])
    
    def markAuxiliary(self, ones, all):
        current_write = 0
        end_write = all*self.conf.BALL_SIZE
        while current_write < end_write:
            bin = self.bins_ram.readChunks([(current_write, current_write + self.conf.BIN_SIZE_IN_BYTES)])
            for i,ball in enumerate(bin):
                assignment = random.uniform(0, 1) < ones/all
                if assignment:
                    bin[i] = self.byte_operations.switchToSecondStatus(ball)
                    ones -= 1
                all -= 1
            self.bins_ram.writeChunks([(current_write, current_write + self.conf.BIN_SIZE_IN_BYTES)], bin)
            current_write += self.conf.BIN_SIZE_IN_BYTES
    
    
    def intersperseRD(self):
        self.markAuxiliary(self.reals_count, self.conf.N)
        self.tightCompaction(int(self.conf.NUMBER_OF_BINS/2), self.bins_ram, [self.conf.SECOND_DATA_STATUS, self.conf.SECOND_DUMMY_STATUS])