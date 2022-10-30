


import math
from RAM.ram import RAM
from config import config
from hashTable import HashTable
from utils.cuckoo_hash import CuckooHash
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
        
    def access(self, op,  key, value = None) -> bytes:
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
        
        # something must always be added to the stash
        if not is_found or key in self.local_stash.keys():
            dummy_data_ball = get_random_string(self.conf.BALL_SIZE,self.conf.BALL_STATUS_POSITION, self.conf.DUMMY_DATA_STATUS)
            self.local_stash[dummy_data_ball[self.conf.BALL_STATUS_POSITION+1:]] = dummy_data_ball

        if not is_found:
            print(f'key {key} not found')    
        elif op == 'read':
            self.local_stash[ball[self.conf.BALL_STATUS_POSITION+1:]] = ball
        elif op == 'write':
            self.local_stash[ball[self.conf.BALL_STATUS_POSITION+1:]] = value + self.conf.DATA_STATUS + ball[self.conf.BALL_STATUS_POSITION+1:]
        self.read_count += 1
        if self.read_count == self.conf.MU:
            self.rebuild()
    
    def rebuild(self):
        self.read_count = 0
        if not self.tables[0].is_built:
            self.rebuildLevelOne()
            return
        for table in self.tables:
            if table.is_built:
                table.binsTightCompaction()
            else:
                break
        
        self.intersperseStashAndLevelOne()
        for i in range(1, len(self.tables[1:])):
            previous_table = self.tables[i-1]
            current_table = self.tables[i]
            if current_table.is_built:
                current_table.copyToEndOfBins(previous_table.bins_ram)
                current_table.intersperse()
                current_table.is_built = False
            else:
                current_table.data_ram = previous_table.bins_ram
                current_table.rebuild()
                return
        final_table = self.tables[-1]
        final_table.binsTightCompaction(self.conf.DUMMY_DATA_STATUS)
        final_table.data_ram, final_table.bins_ram = final_table.bins_ram, final_table.data_ram
        final_table.rebuild()
        
        
                
    
    def intersperseStashAndLevelOne(self):
        hash_table_one = self.tables[0]
        stash_balls = list(self.local_stash.values())
        # stash_balls = hash_table_one.byte_operations.changeBallsStatus(stash_balls, self.conf.SECOND_DATA_STATUS)
        hash_table_one.bins_ram.writeChunks([hash_table_one.conf.MU, 2*hash_table_one.conf.MU], stash_balls)
        hash_table_one.intersperse()
        hash_table_one.is_built = False
    
    def rebuildLevelOne(self):
        hash_table_one = self.tables[0]
        cuckoo_hash = CuckooHash(hash_table_one.conf)
        cuckoo_hash.insert_bulk(list(self.local_stash.values()))
        hash_table_one.bins_ram.writeChunks([[0, hash_table_one.conf.BIN_SIZE_IN_BYTES]], cuckoo_hash.table1 + cuckoo_hash.table2)
        hash_table_one.local_stash = hash_table_one.byte_operations.ballsToDictionary(cuckoo_hash.stash)
        hash_table_one.is_built = True
        
        
            
# What's missing:
# 2. implement intersperse - mind the gaps filled with dummies.