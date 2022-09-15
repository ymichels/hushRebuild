from RAM.ram import RAM
from collections import defaultdict
from utils.byte_operations import ByteOperations
from config import BALL_SIZE, BIN_SIZE, BIN_SIZE_IN_BYTES, BINS_LOCATION, DATA_LOCATION, DATA_SIZE, DATA_STATUS, DUMMY_STATUS, EPSILON, LOCAL_MEMORY_SIZE, LOG_LAMBDA, MAIN_KEY, MU, N, NUMBER_OF_BINS, OVERFLOW_LOCATION, STASH_SIZE
from thresholdGenerator import ThresholdGenerator
from utils.cuckoo_hash import CuckooHash
from utils.helper_functions import get_random_string

class Rebuild:

    def __init__(self) -> None:
        self.byte_operations = ByteOperations(MAIN_KEY)
        self.data_ram = RAM(DATA_LOCATION)
        self.bins_ram = RAM(BINS_LOCATION)
        self.overflow_ram = RAM(OVERFLOW_LOCATION)
        self.threshold_generator = ThresholdGenerator()
        self.dummy = b'\x00'*BALL_SIZE

    # This function creates random data for testing.
    def createReadMemory(self):
        current_write = 0
        while current_write < DATA_SIZE:
            random_bin = [get_random_string(BALL_SIZE,DATA_STATUS) for i in range(BIN_SIZE)]
            self.data_ram.writeChunks(
                [(current_write, current_write + BIN_SIZE_IN_BYTES)], random_bin)
            current_write += BIN_SIZE_IN_BYTES
    
    # This function prepares the bins for writing.
    # It fills the bins with empty values.
    def cleanWriteMemory(self):
        # #Cleaning the bins
        current_write = 0
        empty_bin = [self.dummy]*BIN_SIZE
        while current_write < DATA_SIZE*2:
            self.bins_ram.writeChunks(
                [(current_write, current_write + BIN_SIZE_IN_BYTES)], empty_bin)
            current_write += BIN_SIZE_IN_BYTES
        
        #Cleaning the overflow pile
        current_write = 0
        while current_write < EPSILON*DATA_SIZE*2:
            self.overflow_ram.writeChunks(
                [(current_write, current_write + BIN_SIZE_IN_BYTES)], empty_bin)
            current_write += BIN_SIZE_IN_BYTES
        

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
        distance_from_center = 1/2
        midLocation = int(EPSILON*N)*BALL_SIZE
        
        while offset >= 1:
            start_loc = int(midLocation - midLocation*distance_from_center)
            end_loc = midLocation + midLocation*distance_from_center
            self._tightCompaction(start_loc, end_loc, int(offset))
            
            offset /= 2
            distance_from_center /=2
    
    def _tightCompaction(self, startLoc, endLoc, offset):
        for i in range(offset):
            balls = self.byte_operations.readTransposed(self.overflow_ram, offset, startLoc + i*BALL_SIZE, 2*MU)
            balls = self.localTightCompaction(balls)
            self.byte_operations.writeTransposed(self.overflow_ram, balls, offset, startLoc + i*BALL_SIZE)
        
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
        while current_bin < NUMBER_OF_BINS:
            #Step 1: read how much each bin is full
            #we can read 1/EPSILON bins at a time since from each bin we read 2*EPSILON*MU balls
            capacity_chunks = [(i*BIN_SIZE_IN_BYTES,i*BIN_SIZE_IN_BYTES + BALL_SIZE) for i in range(current_bin, current_bin + int(1/EPSILON))]
            bins_capacity = self.bins_ram.readChunks(capacity_chunks)
            # bins_capacity is a list of int, each int indicates how many balls in the bin
            bins_capacity = [int.from_bytes(bin_capacity, 'big', signed=False) for bin_capacity in bins_capacity]
            
            #Step 2: read the 2*MU*EPSILON top balls from each bin
            chunks = []
            for index,capacity in enumerate(bins_capacity):
                bin_num = index + current_bin
                end_of_bin = bin_num*BIN_SIZE_IN_BYTES + BALL_SIZE*(capacity+1)
                end_of_bin_minus_epsilon = end_of_bin - int(2*MU*EPSILON*BALL_SIZE)
                chunks.append((end_of_bin_minus_epsilon,end_of_bin))
            balls = self.bins_ram.readChunks(chunks)
            #bin_tops is a list of lists of balls, each list of balls is the top 2*MU*EPSILON from it's bin
            bin_tops = [balls[x:x+int(2*MU*EPSILON)] for x in range(0, len(balls), int(2*MU*EPSILON))]
            
            #Step 3: select the secret load and write it to the overflow pile
            self._moveSecretLoad(bins_capacity, bin_tops, iteration_num)
            iteration_num += 1
            current_bin += int(1/EPSILON)

    def _moveSecretLoad(self, bins_capacity, bin_tops, iteration_num):
        write_balls = []
        i = 0
        for capacity,bin_top in zip(bins_capacity,bin_tops):
            
            #this is to skip the non-existant bins.
            # Example: 47 bins, epsilon = 1/9.
            # so we pass on 9 bins at a time, but in the last iteration we pass on the last two bins and then we break.
            if iteration_num*(1/EPSILON) + i >= NUMBER_OF_BINS:
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
        write_balls.extend([self.dummy]*(2*MU - len(write_balls)))
        #Write to the overflow transposed (for the tight compaction later)
        self.byte_operations.writeTransposed(self.overflow_ram, write_balls, int(EPSILON*N/MU), iteration_num*BALL_SIZE)

    def ballsIntoBins(self):
        current_read_pos = 0
        while current_read_pos < DATA_SIZE:
            balls = self.data_ram.readChunks(
                [(current_read_pos, current_read_pos + LOCAL_MEMORY_SIZE)])
            self._ballsIntoBins(balls)
            current_read_pos += LOCAL_MEMORY_SIZE

    def _ballsIntoBins(self, balls):
        local_bins_dict = defaultdict(list)
        for ball in balls:
            local_bins_dict[self.byte_operations.ballToPseudoRandomNumber(
                ball, NUMBER_OF_BINS)].append(ball)
        start_locations = [bin_num *
                          BIN_SIZE_IN_BYTES for bin_num in local_bins_dict.keys()]
        bins_capacity = zip(local_bins_dict.keys(),
                           self.bins_ram.readBalls(start_locations))
        write_chunks = []
        write_balls = []
        for bin_num, capacity_ball in bins_capacity:
            capacity = int.from_bytes(capacity_ball, 'big', signed=False)
            if capacity >= 2*MU -1:
                raise Exception("Error, bin is too full")
            bin_loc = bin_num*BIN_SIZE_IN_BYTES
            bin_write_loc = bin_loc + (capacity + 1) * BALL_SIZE
            new_balls = local_bins_dict[bin_num]

            # updating the capacity
            new_capacity_ball = (capacity + len(new_balls)
                               ).to_bytes(BALL_SIZE, 'big')
            write_chunks.append((bin_loc, bin_loc + BALL_SIZE))
            write_balls.append(new_capacity_ball)

            # balls into bin
            write_chunks.append(
                (bin_write_loc, bin_write_loc + len(new_balls)*BALL_SIZE))
            write_balls.extend(new_balls)
        self.bins_ram.writeChunks(write_chunks,write_balls)

    def cuckooHashBins(self):
        5+5
        current_bin_index = 0
        iteration_num = 0
        overflow_written = 0
        stashes = []
        while current_bin_index < NUMBER_OF_BINS:
            print(current_bin_index)
            # get the bin
            bin_data = self.bins_ram.readChunks([(current_bin_index*BIN_SIZE_IN_BYTES, (current_bin_index +1)*BIN_SIZE_IN_BYTES )])
            capacity = int.from_bytes(bin_data[0], 'big', signed=False)
            bin_data = bin_data[1:capacity+1]

            # generate the cuckoo hash
            cuckoo_hash = CuckooHash()
            cuckoo_hash.insert_bulk(bin_data)

            # write the data
            hash_tables = cuckoo_hash.table1 + cuckoo_hash.table2
            self.bins_ram.writeChunks([(current_bin_index*BIN_SIZE_IN_BYTES, (current_bin_index +1)*BIN_SIZE_IN_BYTES )],hash_tables)
            
            # write the stash
            print('stash:', len(cuckoo_hash.stash))
            dummies = [get_random_string(BALL_SIZE,DUMMY_STATUS) for i in range(STASH_SIZE - len(cuckoo_hash.stash))]
            stashes += cuckoo_hash.stash + dummies
            if len(stashes) + STASH_SIZE >= BIN_SIZE:
                stashes = stashes + [self.dummy]*(BIN_SIZE- len(stashes))
                self.overflow_ram.writeChunks([(int(DATA_SIZE*EPSILON) + overflow_written*BIN_SIZE_IN_BYTES, int(DATA_SIZE*EPSILON) + (overflow_written +1)*BIN_SIZE_IN_BYTES )],stashes)
                stashes = []
                overflow_written += 1
            current_bin_index += 1
        self.overflow_ram.writeChunks([(int(DATA_SIZE*EPSILON) + overflow_written*BIN_SIZE_IN_BYTES, int(DATA_SIZE*EPSILON) + overflow_written*BIN_SIZE_IN_BYTES + len(stashes) )],stashes)
        