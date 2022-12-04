import math
from PathORAM.config import config
from RAM.file_RAM import file_RAM
from hashTable import HashTable
from utils.cuckoo_hash import CuckooHash
from utils.helper_functions import get_random_string
import random

class CruchORAM:
    def __init__(self, number_of_blocks) -> None:
        self.number_of_blocks = number_of_blocks
        self.conf = config(number_of_blocks)
        self.dic = {}

    def position_map_access(self, key):
        old_leaf = random.randint(0,self.number_of_blocks*self.conf.X-1) if key not in self.dic else self.dic[key]
        self.dic[key] = random.randint(0,self.number_of_blocks*self.conf.X-1)
        return old_leaf, self.dic[key]
