from Cryptodome.Cipher import AES
from RAM.ram import RAM
from config import config
from utils.byte_operations import ByteOperations


class CuckooHash:
    def __init__(self, conf:config) -> None:
        self.conf = conf
        self.table1_byte_operations = ByteOperations(self.conf.CUCKOO_HASH_KEY_1)
        self.table2_byte_operations = ByteOperations(self.conf.CUCKOO_HASH_KEY_2)
        self.dummy = b'\x00'*self.conf.BALL_SIZE
        self.table1 = [self.dummy]*self.conf.MU
        self.table2 = [self.dummy]*self.conf.MU
        self.stash = []

    def insert_bulk(self,balls):
        for ball in balls:
            self.insert_ball(ball)
    
    def insert_ball(self,ball):
        seen_locations = []
        while True:
            location = self.table1_byte_operations.ballToPseudoRandomNumber(ball,self.conf.MU)
            evicted_ball = self.table1[location]
            self.table1[location] = ball
            if evicted_ball == self.dummy:
                break
            ball = evicted_ball
            location = self.table2_byte_operations.ballToPseudoRandomNumber(ball,self.conf.MU)
            evicted_ball = self.table2[location]
            self.table2[location] = ball
            if evicted_ball == self.dummy:
                break
            ball = evicted_ball
            if len(seen_locations) > 2*self.conf.MU:
                self.stash.append(ball)
                if len(self.stash) > self.conf.STASH_SIZE:
                    raise Exception("Error, Cuckoo hash stash is full")
                break
            seen_locations.append(location)
            
                