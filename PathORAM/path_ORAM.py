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
        self.local_stash = []
        self.dummy = b'\x00'*self.conf.BALL_SIZE
        # to change
        self.position_map = CruchORAM(int(number_of_blocks/2))
    
    def allocate_memory(self):
        current_write = 0
        empty_memory = [b'\x00'*self.conf.BALL_SIZE]*self.conf.LOCAL_MEMORY_SIZE_IN_BALLS
        while current_write < self.conf.DATA_SIZE:
            self.ram.writeChunks(
                [(current_write, current_write + self.conf.LOCAL_MEMORY_SIZE)], empty_memory)
            current_write += self.conf.LOCAL_MEMORY_SIZE
    
    def access(self, op, key, data = None):
        leaf = self.position_map.position_map_access(key)
        chunks = self.generate_path_chunks(leaf)
        result = None
        path = self.ram.readChunks(chunks)
        for i, ball in enumerate(path):
            if ball != self.dummy and self.check_key(ball, key):
                ball = self.set_random_leaf(ball)
                result = self.get_ball_data(ball)
                if op == 'write':
                    ball = self.change_ball_data(ball, data)
                path[i] = ball
        if op == 'write' and result == None:
            self.local_stash.append(self.create_ball(key, data))
        levels = int(len(path)/self.conf.Z)
        self.local_stash.extend(filter(lambda a: a != self.dummy, path))
        write_back = []
        for i in range(levels):
            bucket = []
            for ball in self.local_stash:
                if int(self.get_leaf(ball)/(2**i)) == int(leaf/(2**i)):
                    bucket.append(ball)
                    self.local_stash.remove(ball)
                    if len(bucket) == self.conf.Z:
                        break
            write_back.extend(self.complete_bucket(bucket))

        self.ram.writeChunks(chunks, write_back)
        return result

    def create_ball(self, key, data):
        ball = key.to_bytes(self.conf.KEY_SIZE, 'big') + b'\x00'*(self.conf.KEY_SIZE + self.conf.DATA_SIZE)
        ball = self.set_random_leaf(ball)
        ball = self.change_ball_data(ball, data)
        return ball

    
    def get_ball_data(self, ball):
        return ball[self.conf.KEY_SIZE*2:]

    def complete_bucket(self, bucket):
        return bucket + [self.dummy]*(self.conf.Z - len(bucket))

    def get_leaf(self, ball):
        return self.bytes_to_int(ball[self.conf.KEY_SIZE:2*self.conf.KEY_SIZE])

    def change_ball_data(self, ball, data):
        return ball[:self.conf.KEY_SIZE*2] + data
    
    def set_random_leaf(self, ball):
        return ball[:self.conf.KEY_SIZE] + random.randint(0, self.conf.N-1).to_bytes(self.conf.KEY_SIZE, 'big') + ball[self.conf.KEY_SIZE*2:]
    
    def bytes_to_int(self, _bytes):
        return int.from_bytes(_bytes, 'big', signed=False)

    def check_key(self, ball, key):
        byte_key = ball[:self.conf.KEY_SIZE]
        return self.bytes_to_int(byte_key) == key

    def generate_path_chunks(self, leaf):
        chunks = []
        starting_point = 0
        advance = self.conf.N
        while advance >= 1:
            chunks.append((starting_point + leaf*self.conf.BUCKET_SIZE, starting_point + leaf*self.conf.BUCKET_SIZE + self.conf.BUCKET_SIZE))
            starting_point += int(advance*self.conf.BUCKET_SIZE)
            advance /= 2
            leaf = int(leaf/2)
        return chunks


    def position_map_access(self, key):
        raise 'not implemented'
    


