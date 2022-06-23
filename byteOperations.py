from Cryptodome.Cipher import AES
from config import NUMBER_OF_BINS


class ByteOperations:
    def __init__(self) -> None:
        key = b'Sixteen byte key'
        self.cipher = AES.new(key, AES.MODE_ECB)

    def ballToBinIndex(self, ball):
        enc = self.cipher.encrypt(ball)
        return int.from_bytes(enc, 'big', signed=False) % NUMBER_OF_BINS

