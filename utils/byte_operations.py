from Cryptodome.Cipher import AES
from RAM.ram import RAM
from config import config


class ByteOperations:
    def __init__(self,key, conf:config) -> None:
        self.conf = conf
        self.key_length = len(key)
        self.cipher = AES.new(key, AES.MODE_ECB)

    
    def isBitOn(self, number, bit_num):
        return (number & (2**bit_num)) > 0


    def getCapacity(self, capacity_ball):
        if capacity_ball[self.conf.BALL_STATUS_POSITION: self.conf.BALL_STATUS_POSITION + 1] != self.conf.DUMMY_STATUS:
            return 0
        else:
            int.from_bytes(capacity_ball, 'big', signed=False)
        
        
    def ballToPseudoRandomNumber(self, ball,limit = -1):
        ball_key = ball[self.conf.BALL_STATUS_POSITION + 1:]
        return self.keyToPseudoRandomNumber(ball_key, limit)
        
    def keyToPseudoRandomNumber(self, key,limit=-1):
        if len(key) % self.key_length != 0:
            key += b'\x00'*(self.key_length - len(key) % self.key_length)
        enc = self.cipher.encrypt(key)
        if limit == -1:
            return int.from_bytes(enc, 'big', signed=False)
        return int.from_bytes(enc, 'big', signed=False) % limit
    
    def writeTransposed(self, ram: RAM, balls, offset, start):
        chunks = []
        for i in range(len(balls)):
            chunks.append((start + i*offset*self.conf.BALL_SIZE, start + i*offset*self.conf.BALL_SIZE + self.conf.BALL_SIZE))
        ram.writeChunks(chunks, balls)

    def readTransposed(self, ram: RAM, offset, start, readLength):
        chunks = []
        for i in range(readLength):
            chunks.append((start + i*offset*self.conf.BALL_SIZE, start + i*offset*self.conf.BALL_SIZE + self.conf.BALL_SIZE))
        return ram.readChunks(chunks)
   
    
    def removeSecondDataStatus(self, balls):
        result = []
        for ball in balls:
            if ball[self.conf.BALL_STATUS_POSITION: self.conf.BALL_STATUS_POSITION + 1] == self.conf.SECOND_DATA_STATUS:
                result.append(self.changeBallStatus(ball, self.conf.DATA_STATUS))
            elif ball[self.conf.BALL_STATUS_POSITION: self.conf.BALL_STATUS_POSITION + 1] == self.conf.DUMMY_SECOND_DATA_STATUS:
                result.append(self.changeBallStatus(ball, self.conf.DUMMY_DATA_STATUS))
            else:
                result.append(ball)
        return result
     
    def changeBallsStatus(self, balls, status):
        return [self.changeBallStatus(ball, status) for ball in balls]
    
    def changeBallStatus(self, ball, status):
        return ball[:self.conf.BALL_STATUS_POSITION] + status + ball[1 + self.conf.BALL_STATUS_POSITION:]
    
    def ballsToDictionary(self, balls):
        dic = {}
        for ball in balls:
            dic[ball[1 + self.conf.BALL_STATUS_POSITION:]] = ball
        return dic
            
            
            
            