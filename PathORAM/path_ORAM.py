import math
from PathORAM.config import config
from PathORAM.cruch_oram import CruchORAM
from RAM.ram import RAM
from hashTable import HashTable
from utils.cuckoo_hash import CuckooHash
from utils.helper_functions import get_random_string
import random

class PathORAM:

    def __init__(self, number_of_blocks) -> None:
        self.number_of_blocks = 2**math.ceil(math.log(number_of_blocks,2))
        self.conf = config(number_of_blocks)
        self.ram = RAM('path_oram_data/{}.txt'.format(math.log(number_of_blocks,2)), self.conf)
        self.empty_memory = [b'\x00'*self.conf.BALL_SIZE]*self.conf.LOCAL_MEMORY_SIZE_IN_BALLS
        # to change
        self.position_map = CruchORAM(number_of_blocks/2)
    
    def allocate_memory(self):
        current_write = 0
        while current_write < self.conf.DATA_SIZE:
            self.ram.writeChunks(
                [(current_write, current_write + self.conf.LOCAL_MEMORY_SIZE)], self.empty_memory)
            current_write += self.conf.LOCAL_MEMORY_SIZE
