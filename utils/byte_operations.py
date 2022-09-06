from Cryptodome.Cipher import AES
from RAM.ram import RAM
from config import BALL_SIZE, BALL_STATUS_POSITION, BIN_SIZE, MU, NUMBER_OF_BINS


class ByteOperations:
    def __init__(self,key) -> None:
        self.key_length = len(key)
        self.cipher = AES.new(key, AES.MODE_ECB)

    
    def ballToPseudoRandomNumber(self, ball,limit=-1):
        ball_key = ball[BALL_STATUS_POSITION+1:]
        if len(ball_key) % self.key_length != 0:
            ball_key += b'\x00'*(self.key_length - len(ball_key) % self.key_length)
        enc = self.cipher.encrypt(ball_key)
        if limit == -1:
            return int.from_bytes(enc, 'big', signed=False)
        return int.from_bytes(enc, 'big', signed=False) % limit
    
    def writeTransposed(self, ram: RAM, balls, offset, start):
        chunks = []
        for i in range(len(balls)):
            chunks.append((start + i*offset*BALL_SIZE, start + i*offset*BALL_SIZE + BALL_SIZE))
        ram.writeChunks(chunks, balls)

    def readTransposed(self, ram: RAM, offset, start, readLength):
        chunks = []
        for i in range(readLength):
            chunks.append((start + i*offset*BALL_SIZE, start + i*offset*BALL_SIZE + BALL_SIZE))
        return ram.readChunks(chunks)