from config import config
import random
from utils.byte_operations import ByteOperations

class CuckooHash:
    def createDummies(self, count):
        return [self.dummy]*count
    
    def __init__(self, conf:config) -> None:
        self.conf = conf
        self.dummy = conf.DUMMY_STATUS*conf.BALL_SIZE
        self.table1_byte_operations = ByteOperations(self.conf.CUCKOO_HASH_KEY_1, conf)
        self.table2_byte_operations = ByteOperations(self.conf.CUCKOO_HASH_KEY_2, conf)
        self.table1 = self.createDummies(self.conf.MU)
        self.table2 = self.createDummies(self.conf.MU)
        self.stash = []

    def insert_bulk(self,balls):
        random.shuffle(balls)
        for ball in balls:
            if ball[self.conf.BALL_STATUS_POSITION: self.conf.BALL_STATUS_POSITION+1] == self.conf.DUMMY_STATUS:
                continue
            self.insert_ball(ball)
        print('stash size: ', len(self.stash))
    
    def insert_ball(self,ball):
        seen_locations = []
        while True:
            location = self.table1_byte_operations.ballToPseudoRandomNumber(ball,self.conf.MU)
            evicted_ball = self.table1[location]
            self.table1[location] = ball
            if evicted_ball[self.conf.BALL_STATUS_POSITION: self.conf.BALL_STATUS_POSITION+1] == self.conf.DUMMY_STATUS:
                break
            ball = evicted_ball
            location = self.table2_byte_operations.ballToPseudoRandomNumber(ball,self.conf.MU)
            evicted_ball = self.table2[location]
            self.table2[location] = ball
            if evicted_ball[self.conf.BALL_STATUS_POSITION: self.conf.BALL_STATUS_POSITION+1] == self.conf.DUMMY_STATUS:
                break
            ball = evicted_ball
            if len(seen_locations) > 2*self.conf.MU:
                if ball[self.conf.BALL_STATUS_POSITION: self.conf.BALL_STATUS_POSITION+1] == self.conf.DATA_STATUS:
                    stash_ball = self.table1_byte_operations.changeBallStatus(ball, self.conf.STASH_DATA_STATUS)                
                    self.stash.append(stash_ball)
                    if len(self.stash) > self.conf.STASH_SIZE:
                        raise Exception("Error, Cuckoo hash stash is full")
                break
            seen_locations.append(location)
            
    def get_possible_addresses(self, key):
        table1_location = self.table1_byte_operations.keyToPseudoRandomNumber(key, self.conf.MU)
        table2_location = self.table2_byte_operations.keyToPseudoRandomNumber(key, self.conf.MU)
        return table1_location, table2_location