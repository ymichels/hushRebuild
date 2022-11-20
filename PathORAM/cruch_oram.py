import math
from RAM.ram import RAM
from config import config
from hashTable import HashTable
from utils.cuckoo_hash import CuckooHash
from utils.helper_functions import get_random_string
import random

class CruchORAM:
    def __init__(self, number_of_blocks) -> None:
        self.dic = {}

    def access(self, op, key, data):
        if op == 'write':
            self.dic[key] = data
        return self.dic[key]
