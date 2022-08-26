from Cryptodome.Cipher import AES
from RAM.ram import RAM
from config import BALL_SIZE, BIN_SIZE, CUCKOO_HASH_KEY_1, CUCKOO_HASH_KEY_2, MU, NUMBER_OF_BINS
from utils.byte_operations import ByteOperations


class CuckooHash:
    def __init__(self) -> None:
        self.table1_byte_operations = ByteOperations(CUCKOO_HASH_KEY_1)
        self.table2_byte_operations = ByteOperations(CUCKOO_HASH_KEY_2)
        dummy = b'\x00'*BALL_SIZE
        self.table1 = [self.dummy]*(BIN_SIZE/2)
        self.table2 = [self.dummy]*(BIN_SIZE/2)

    def insert_bulk(balls):
        for ball in balls: