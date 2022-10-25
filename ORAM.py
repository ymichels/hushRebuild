


import math
from RAM.ram import RAM
from config import config
from hashTable import HashTable
from utils.helper_functions import get_random_string


class ORAM:

    def __init__(self, number_of_blocks) -> None:
        
        # power of two number of bins:
        number_of_blocks = (2**math.ceil(math.log(number_of_blocks/config.MU,2)))*config.MU
        self.conf = config(number_of_blocks)
        self.dummy = b'\x00'*self.conf.BALL_SIZE
        
        self.local_stash = {}
        
        self.read_count = 0
        self.tables:list[HashTable]= []
        current_number_of_blocks = config.MU
        while current_number_of_blocks <= number_of_blocks:
            self.tables.append(HashTable(config(current_number_of_blocks)))
            current_number_of_blocks *= 2
            
    
    def cleanWriteMemory(self):
        for table in self.tables:
            table.cleanWriteMemory()
    
    def initial_build(self, data_location) -> None:
        final_table = self.tables[-1]
        temp = final_table.data_ram
        final_table.data_ram = RAM(data_location, final_table.conf)
        final_table.rebuild()
        final_table.data_ram = temp
        
    def access(self, op,  key, value) -> bytes:
        # search local stash
        is_found = False
        ball = self.local_stash.get(key)
        if ball != None:
            is_found = True
            key = get_random_string(self.conf.BALL_SIZE - self.conf.BALL_STATUS_POSITION -1)
        
        # search tables
        for table in self.tables:
            if table.is_built and not is_found:
                ball = table.lookup(key)
                if ball[self.conf.BALL_STATUS_POSITION+1:] == key:
                    is_found = True
                    key = get_random_string(self.conf.BALL_SIZE - self.conf.BALL_STATUS_POSITION -1)
            elif table.is_built and is_found:
                table.lookup(key)
        
        if not is_found:
            print('key {} not found'.format(key))
        elif op == 'read':
            self.local_stash[ball[self.conf.BALL_STATUS_POSITION+1:]] = ball
        elif op == 'write':
            self.local_stash[ball[self.conf.BALL_STATUS_POSITION+1:]] = value + self.conf.DATA_STATUS + ball[self.conf.BALL_STATUS_POSITION+1:]
        self.read_count += 1
        if self.read_count == self.conf.MU:
            self.rebuild()
    
    def rebuild(self):
        5+5
        
            
    
    
    