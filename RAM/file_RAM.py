import math
from config import baseConfig
import os
from pathlib import Path

class file_RAM:
    RAM_TYPE = 'file'
    BALL_READ = 0
    BALL_WRITE = 0
    RT_READ = 0
    RT_WRITE = 0
    
    def __init__(self, file_path, conf:baseConfig) -> None:
        self.conf = conf
        self.file_path = file_path
        output_file = Path(file_path)
        if not os.path.isfile(file_path):
            output_file.parent.mkdir(exist_ok=True, parents=True)
            output_file.write_text("")
        self.file = open(file_path, 'r+b')


    def readBall(self, location):
        file_RAM.BALL_READ += 1
        if file_RAM.BALL_READ % 1_000_000 == 0:
            print('RAM.BALL_READ: ', file_RAM.BALL_READ)
            
        self.file.seek(location)
        return self.file.read(self.conf.BALL_SIZE)

    def writeBall(self, location, ball):
        file_RAM.BALL_WRITE += 1
        if file_RAM.BALL_WRITE % 1_000_000 == 0:
            print('RAM.BALL_WRITE: ', file_RAM.BALL_WRITE)
        self.file.seek(location)
        self.file.write(ball)
    
    def readChunk(self, chunk):
        start, end = chunk
        balls_num = int((end-start)/self.conf.BALL_SIZE)
        file_RAM.BALL_READ += balls_num
        if int((file_RAM.BALL_READ - balls_num) / 1_000_000) != int(file_RAM.BALL_READ / 1_000_000):
            print('RAM.BALL_READ: ', file_RAM.BALL_READ)
        self.file.seek(start)
        chunk_bytes = self.file.read(balls_num*self.conf.BALL_SIZE)
        chunk_balls = [chunk_bytes[i*self.conf.BALL_SIZE:(i+1)*self.conf.BALL_SIZE] for i in range(balls_num)]
        chunk_balls.append(b'')
        chunk_balls = chunk_balls[:chunk_balls.index(b'')]
        return chunk_balls
    
    def writeChunk(self, chunk, balls):
        start, end = chunk
        balls_num = int((end-start)/self.conf.BALL_SIZE)
        file_RAM.BALL_WRITE += balls_num
        if int((file_RAM.BALL_WRITE - balls_num) / 1_000_000) != int(file_RAM.BALL_WRITE / 1_000_000):
            print('RAM.BALL_WRITE: ', file_RAM.BALL_WRITE)
        self.file.seek(start)
        to_write = b''.join(balls)
        if len(to_write) != len(balls)*self.conf.BALL_SIZE:
            raise 'here!!!'
        self.file.write(b''.join(balls))
        # return [chunk_bytes[i*self.conf.BALL_SIZE:(i+1)*self.conf.BALL_SIZE] for i in range(balls_num)]
        

    def readChunks(self, chunks):
        file_RAM.RT_READ += 1
        if file_RAM.RT_READ % 1_000_000 == 0:
            print('RAM.RT_READ: ', file_RAM.RT_READ)
        balls = []
        for chunk in chunks:
            chunk_balls = self.readChunk(chunk)
            balls.extend(chunk_balls)
            # read_balls = []
            # start, end = chunk
            # while start < end:
            #     read_balls.append(self.readBall(start))
            #     start += self.conf.BALL_SIZE
            # balls.extend(read_balls)
        return balls

    def writeChunks(self, chunks, balls):
        file_RAM.RT_WRITE += 1
        if file_RAM.RT_WRITE % 1_000_000 == 0:
            print('RAM.RT_WRITE: ', file_RAM.RT_WRITE)
        i = 0
        for chunk in chunks:
            start, end = chunk
            balls_num = math.ceil((end-start)/self.conf.BALL_SIZE)
            self.writeChunk(chunk, balls[i:i+balls_num])
            i += balls_num
            # while start < end:
            #     self.writeBall(start, balls[i])
            #     start += self.conf.BALL_SIZE
            #     i += 1
        return balls

    def readBalls(self, locations):
        file_RAM.RT_READ += 1
        if file_RAM.RT_READ % 1_000_000 == 0:
            print('RAM.RT_READ: ', file_RAM.RT_READ)
        return [self.readBall(location) for location in locations]
    
    def appendBalls(self, balls):
        self.file.seek(0,2)
        self.file.write(b''.join(balls))

    def getSize(self):
        if self.conf.FINAL:
            return 2*self.conf.DATA_SIZE
        return self.conf.DATA_SIZE