import math
from config import baseConfig
import os
from utils.helper_functions import get_random_string
from pathlib import Path

class local_RAM:
    BALL_READ = 0
    BALL_WRITE = 0
    RT_READ = 0
    RT_WRITE = 0
    
    def __init__(self, file_path, conf:baseConfig) -> None:
        self.conf = conf
        self.file_path = file_path
        self.memory = []


    def readBall(self, location):
        local_RAM.BALL_READ += 1
        if local_RAM.BALL_READ % 1_000_000 == 0:
            print('RAM.BALL_READ: ', local_RAM.BALL_READ)

        return self.memory[int(location/self.conf.BALL_SIZE)]


    def writeBall(self, location, ball):
        local_RAM.BALL_WRITE += 1
        if local_RAM.BALL_WRITE % 1_000_000 == 0:
            print('RAM.BALL_WRITE: ', local_RAM.BALL_WRITE)
        
        self.memory[int(location/self.conf.BALL_SIZE)] = ball
    
    def readChunk(self, chunk):
        start, end = chunk
        balls_num = int((end-start)/self.conf.BALL_SIZE)
        local_RAM.BALL_READ += balls_num
        if int((local_RAM.BALL_READ - balls_num) / 1_000_000) != int(local_RAM.BALL_READ / 1_000_000):
            print('RAM.BALL_READ: ', local_RAM.BALL_READ)
    
        return self.memory[int(start/self.conf.BALL_SIZE):int(end/self.conf.BALL_SIZE)]
    
    def writeChunk(self, chunk, balls):
        start, end = chunk
        balls_num = int((end-start)/self.conf.BALL_SIZE)
        local_RAM.BALL_WRITE += balls_num
        if int((local_RAM.BALL_WRITE - balls_num) / 1_000_000) != int(local_RAM.BALL_WRITE / 1_000_000):
            print('RAM.BALL_WRITE: ', local_RAM.BALL_WRITE)
        
        ball_start = int(start/self.conf.BALL_SIZE)
        if ball_start >= len(self.memory):
            self.memory.extend(balls)
        else:
            self.memory[ball_start:ball_start + len(balls)] = balls
        
        

    def readChunks(self, chunks):
        local_RAM.RT_READ += 1
        if local_RAM.RT_READ % 1_000_000 == 0:
            print('RAM.RT_READ: ', local_RAM.RT_READ)
        balls = []
        for chunk in chunks:
            chunk_balls = self.readChunk(chunk)
            balls.extend(chunk_balls)
        return balls

    def writeChunks(self, chunks, balls):
        local_RAM.RT_WRITE += 1
        if local_RAM.RT_WRITE % 1_000_000 == 0:
            print('RAM.RT_WRITE: ', local_RAM.RT_WRITE)
        i = 0
        for chunk in chunks:
            start, end = chunk
            balls_num = math.ceil((end-start)/self.conf.BALL_SIZE)
            self.writeChunk(chunk, balls[i:i+balls_num])
            i += balls_num
        return balls

    def readBalls(self, locations):
        local_RAM.RT_READ += 1
        if local_RAM.RT_READ % 1_000_000 == 0:
            print('RAM.RT_READ: ', local_RAM.RT_READ)
        return [self.readBall(location) for location in locations]

    def getSize(self):
        if self.conf.FINAL:
            return 2*self.conf.DATA_SIZE
        return self.conf.DATA_SIZE

    def generate_random_memory(self, number_of_balls):
        self.memory = [get_random_string(self.conf.BALL_SIZE, self.conf.BALL_STATUS_POSITION, self.conf.DATA_STATUS) for _ in range(number_of_balls)]
        print('finished generation')