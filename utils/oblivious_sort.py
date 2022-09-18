from config import BALL_SIZE, BIN_SIZE, MAIN_KEY
from utils.byte_operations import ByteOperations


class ObliviousSort:
    def __init__(self) -> None:
        self.byte_operations = ByteOperations(MAIN_KEY)
        self.dummy = b'\x00'*BALL_SIZE

    def splitToBinsByBit(self, balls, bit_num, number_of_bins):
        bin_zero = []
        bin_one = []
        for ball in balls:
            if ball == self.dummy:
                continue
            assigned_bin = self.byte_operations.ballToPseudoRandomNumber(ball, number_of_bins)
            bit = self.byte_operations.isBitOn(assigned_bin, bit_num)
            if bit:
                bin_one.append(ball)
            else:
                bin_zero.append(ball)
        bin_one = bin_one + [self.dummy] * (BIN_SIZE - len(bin_one))
        bin_zero = bin_zero + [self.dummy] * (BIN_SIZE - len(bin_zero))
        return bin_zero, bin_one
        

