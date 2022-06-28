from config import BALL_SIZE


class RAM:
    def __init__(self, fileName) -> None:
        self.file = open(fileName, 'r+b')

    def readBall(self, location):
        self.file.seek(location)
        return self.file.read(BALL_SIZE)

    def writeBall(self, location, ball):
        self.file.seek(location)
        self.file.write(ball)

    def readChunks(self, chunks):
        balls = []
        for chunk in chunks:
            start, end = chunk
            while start < end:
                balls.append(self.readBall(start))
                start += BALL_SIZE
        return balls

    def writeChunks(self, chunks, balls):
        i = 0
        for chunk in chunks:
            start, end = chunk
            while start < end:
                self.writeBall(start, balls[i])
                start += BALL_SIZE
                i += 1
        return balls

    def readBalls(self, locations):
        return [self.readBall(location) for location in locations]
    
    def appendBalls(self, balls):
        self.file.seek(0,2)
        self.file.write(b''.join(balls))