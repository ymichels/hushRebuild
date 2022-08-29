from Cryptodome.Cipher import AES
from RAM.ram import RAM
from config import BALL_SIZE, BIN_SIZE, MU, NUMBER_OF_BINS


class ByteOperations:
    def __init__(self,key) -> None:
        self.cipher = AES.new(key, AES.MODE_ECB)

    
    # TODO: 1 byte as data, 1 byte as status, the rest is the key
    def ballToPseudoRandomNumber(self, ball,limit=-1):
        # TODO: only on the key, not the data or status
        enc = self.cipher.encrypt(ball)
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