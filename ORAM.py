


import math
from RAM.ram import RAM
from config import config
from hashTable import HashTable


class ORAM:

    def __init__(self, number_of_blocks) -> None:
        # power of two number of bins:
        number_of_blocks = (2**math.ceil(math.log(number_of_blocks/config.MU,2)))*config.MU
        self.tables:list[HashTable]= []
        current_number_of_blocks = config.MU
        while current_number_of_blocks <= number_of_blocks:
            self.tables.append(HashTable(config(current_number_of_blocks)))
            current_number_of_blocks *= 2
            
    
    def cleanWriteMemory(self):
        for table in self.tables:
            table.cleanWriteMemory()
    
    def initiall_build(self, data_location) -> None:
        final_table = self.tables[-1]
        temp = final_table.data_ram
        final_table.data_ram = RAM(data_location, final_table.conf)
        final_table.rebuild()
        final_table.data_ram = temp
    
    def read(self, key) -> bytes:
        pass
    
    def write(self, key, value) -> bool:
        pass
    
    
    