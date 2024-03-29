import math

from utils.helper_functions import get_random_string

class baseConfig:
    N = 2**20

class config(baseConfig):
    N = 2**20

    
    KEY_SIZE = 16

    #NOTE: because constructCapacityThresholdBall and deconstructCapacityThresholdBall are not well implemented, 
    # this must be an even number. to be corrected in a future version
    BALL_DATA_SIZE = 16
    # the balls structure:  DATA || STATUS || KEY
    BALL_STATUS_POSITION = BALL_DATA_SIZE
    BALL_SIZE = BALL_DATA_SIZE + 1 + KEY_SIZE
    LOG_LAMBDA = 9
    MU = 30*LOG_LAMBDA**3
    NUMBER_OF_BINS = math.ceil(N/MU)
    BIN_SIZE = 2*MU
    BIN_SIZE_IN_BYTES = BIN_SIZE*BALL_SIZE
    EPSILON = 1/LOG_LAMBDA
    STASH_SIZE = 2*LOG_LAMBDA
    FINAL = False

    DATA_SIZE = N*BALL_SIZE
    OVERFLOW_SIZE = math.ceil(DATA_SIZE*EPSILON)
    LOCAL_MEMORY_SIZE = BIN_SIZE_IN_BYTES
    NUMBER_OF_BINS_IN_OVERFLOW = math.ceil(EPSILON*N/MU)

    DATA_LOCATION = 'data.txt'
    BINS_LOCATION = 'bins.txt'
    OVERFLOW_LOCATION = 'overflow.txt'
    
    # This is for the oblivious balls into bins so that the bins would not be overridden.
    OVERFLOW_SECOND_LOCATION = 'second_overflow.txt'
    
    
    MIXED_STRIPE_LOCATION = 'mixed_stripe.txt'

    MAIN_KEY = b'Sixteen byte key'
    CUCKOO_HASH_KEY_1 = b'Cuckoo hash key1'
    CUCKOO_HASH_KEY_2 = b'Cuckoo hash key2'
    
    DUMMY_STATUS = b'\x00'
    DATA_STATUS = b'\x01'
    STASH_DATA_STATUS = b'\x02'
    STASH_DUMMY_STATUS = b'\x03'
    
    # we require a second data status for perposes of intersperse
    SECOND_DATA_STATUS = b'\x04'
    SECOND_DUMMY_STATUS = b'\x05'
    
    def __init__(self, N=None):
        if N == None:
            return
        self.N = N
        self.reset()
        
        self.MAIN_KEY = get_random_string(16)
        self.CUCKOO_HASH_KEY_1 = get_random_string(16)
        self.CUCKOO_HASH_KEY_2 = get_random_string(16)
        
        self.DATA_LOCATION = '{}/data.txt'.format(self.NUMBER_OF_BINS)
        self.BINS_LOCATION = '{}/bins.txt'.format(self.NUMBER_OF_BINS)
        self.OVERFLOW_LOCATION = '{}/overflow.txt'.format(self.NUMBER_OF_BINS)
        # This is for the oblivious balls into bins so that the bins would not be overriden.
        self.OVERFLOW_SECOND_LOCATION = '{}/second_overflow.txt'.format(self.NUMBER_OF_BINS)
        self.MIXED_STRIPE_LOCATION = '{}/mixed_stripe.txt'.format(self.NUMBER_OF_BINS)
        
        
        
    def reset(self):
        self.NUMBER_OF_BINS = math.ceil(self.N/self.MU)
        self.DATA_SIZE = self.N*self.BALL_SIZE
        self.OVERFLOW_SIZE = math.ceil(self.DATA_SIZE*self.EPSILON)
        self.NUMBER_OF_BINS_IN_OVERFLOW = math.ceil(self.EPSILON*self.N/self.MU)
        self.FINAL = False
        
        
# logn = 20
# n = 2**logn
# logLamb = 9
# lamb = 2**logLamb
# mu = 30*logLamb**3
# B = n/mu
# epsilon = 1/logLamb