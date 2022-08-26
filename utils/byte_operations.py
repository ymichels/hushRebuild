from Cryptodome.Cipher import AES
from RAM.ram import RAM
from config import BALL_SIZE, BIN_SIZE, MU, NUMBER_OF_BINS


class ByteOperations:
    def __init__(self,key) -> None:
        key = b'Sixteen byte key'
        self.cipher = AES.new(key, AES.MODE_ECB)

    
    #TODO: use only 90% of the ball as the key
    def ballToLocationInBin(self, ball):
        enc = self.cipher.encrypt(ball)
        return int.from_bytes(enc, 'big', signed=False) % BIN_SIZE
    
    def ballToBinIndex(self, ball):
        enc = self.cipher.encrypt(ball)
        return int.from_bytes(enc, 'big', signed=False) % NUMBER_OF_BINS

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