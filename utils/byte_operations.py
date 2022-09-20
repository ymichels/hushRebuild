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

    def ballToPseudoRandomNumber(self, ball,limit=-1):
        ball_key = ball[self.conf.BALL_STATUS_POSITION+1:]
        if len(ball_key) % self.key_length != 0:
            ball_key += b'\x00'*(self.key_length - len(ball_key) % self.key_length)
        enc = self.cipher.encrypt(ball_key)
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