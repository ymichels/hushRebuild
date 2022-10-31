import math

from utils.helper_functions import get_random_string

class config:
    N = 2**20

    BALL_SIZE = 16
    LOG_LAMBDA = 9
    MU = 30*LOG_LAMBDA**3
    NUMBER_OF_BINS = math.ceil(N/MU)
    BIN_SIZE = 2*MU
    BIN_SIZE_IN_BYTES = BIN_SIZE*BALL_SIZE
    EPSILON = 1/LOG_LAMBDA
    STASH_SIZE = 2*LOG_LAMBDA


    DATA_SIZE = N*BALL_SIZE
    OVERFLOW_SIZE = math.ceil(DATA_SIZE*EPSILON)
    LOCAL_MEMORY_SIZE = BIN_SIZE_IN_BYTES
    NUMBER_OF_BINS_IN_OVERFLOW = math.ceil(EPSILON*N/MU)

    DATA_LOCATION = 'data.txt'
    BINS_LOCATION = 'bins.txt'
    OVERFLOW_LOCATION = 'overflow.txt'
    # This is for the oblivious balls into bins so that the bins would not be overriden.
    OVERFLOW_SECOND_LOCATION = 'second_overflow.txt'

    MAIN_KEY = b'Sixteen byte key'
    CUCKOO_HASH_KEY_1 = b'Cuckoo hash key1'
    CUCKOO_HASH_KEY_2 = b'Cuckoo hash key2'
    
    # the balls structure:  DATA || STATUS || KEY
    BALL_STATUS_POSITION = 4
    DUMMY_STATUS = b'\x00'
    DATA_STATUS = b'\x01'
    STASH_DATA_STATUS = b'\x02'
    STASH_DUMMY_STATUS = b'\x03'
    
    # we require a second data status for perposes of intersperse
    SECOND_DATA_STATUS = b'\x04'
    
    # when adding a dummy that will behave as a real ball until the final layer needs to be rebuilt - when it'll be removed 
    DUMMY_DATA_STATUS = b'\x05'
    DUMMY_SECOND_DATA_STATUS = b'\x06'
    
    def __init__(self, N=None):
        if N == None:
            return
        self.N = N
        self.NUMBER_OF_BINS = math.ceil(N/self.MU)
        self.DATA_SIZE = N*self.BALL_SIZE
        self.OVERFLOW_SIZE = math.ceil(self.DATA_SIZE*self.EPSILON)
        self.NUMBER_OF_BINS_IN_OVERFLOW = math.ceil(self.EPSILON*N/self.MU)
        self.DATA_LOCATION = '{}/data.txt'.format(self.NUMBER_OF_BINS)
        self.BINS_LOCATION = '{}/bins.txt'.format(self.NUMBER_OF_BINS)
        self.OVERFLOW_LOCATION = '{}/overflow.txt'.format(self.NUMBER_OF_BINS)
        # This is for the oblivious balls into bins so that the bins would not be overriden.
        self.OVERFLOW_SECOND_LOCATION = '{}/second_overflow.txt'.format(self.NUMBER_OF_BINS)
        
        self.MAIN_KEY = get_random_string(16)
        self.CUCKOO_HASH_KEY_1 = get_random_string(16)
        self.CUCKOO_HASH_KEY_2 = get_random_string(16)
        
        
# logn = 20
# n = 2**logn
# logLamb = 9
# lamb = 2**logLamb
# mu = 30*logLamb**3
# B = n/mu
# epsilon = 1/logLamb