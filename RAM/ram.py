from config import config
import os
from pathlib import Path
class RAM:
    BALL_READ = 0
    BALL_WRITE = 0
    RT_READ = 0
    RT_WRITE = 0
    
    def __init__(self, file_path, conf:config) -> None:
        self.conf = conf
        self.file_path = file_path
        output_file = Path(file_path)
        if not os.path.isfile(file_path):
            output_file.parent.mkdir(exist_ok=True, parents=True)
            output_file.write_text("")
        # os.makedirs(os.path.dirname(file_path), exist_ok=True)
        self.file = open(file_path, 'r+b')


    def readBall(self, location):
        RAM.BALL_READ += 1
        if RAM.BALL_READ % 1_000_000 == 0:
            print('RAM.BALL_READ: ', RAM.BALL_READ)
            
        self.file.seek(location)
        return self.file.read(self.conf.BALL_SIZE)

    def writeBall(self, location, ball):
        RAM.BALL_WRITE += 1
        if RAM.BALL_WRITE % 1_000_000 == 0:
            print('RAM.BALL_WRITE: ', RAM.BALL_WRITE)
        self.file.seek(location)
        self.file.write(ball)

    def readChunks(self, chunks):
        RAM.RT_READ += 1
        if RAM.RT_READ % 1_000_000 == 0:
            print('RAM.RT_READ: ', RAM.RT_READ)
        balls = []
        for chunk in chunks:
            start, end = chunk
            while start < end:
                balls.append(self.readBall(start))
                start += self.conf.BALL_SIZE
        return balls

    def writeChunks(self, chunks, balls):
        RAM.RT_WRITE += 1
        if RAM.RT_WRITE % 1_000_000 == 0:
            print('RAM.RT_WRITE: ', RAM.RT_WRITE)
        i = 0
        for chunk in chunks:
            start, end = chunk
            while start < end:
                self.writeBall(start, balls[i])
                start += self.conf.BALL_SIZE
                i += 1
        return balls

    def readBalls(self, locations):
        RAM.RT_READ += 1
        if RAM.RT_READ % 1_000_000 == 0:
            print('RAM.RT_READ: ', RAM.RT_READ)
        return [self.readBall(location) for location in locations]
    
    def appendBalls(self, balls):
        self.file.seek(0,2)
        self.file.write(b''.join(balls))

