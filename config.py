import math


N = 2**20

BALL_SIZE = 16
LOG_LAMBDA = 9
MU = 30*LOG_LAMBDA**3
NUMBER_OF_BINS = math.ceil(N/MU)
BIN_SIZE = 2*MU
BIN_SIZE_IN_BYTES = BIN_SIZE*BALL_SIZE
EPSILON = 1/LOG_LAMBDA
STASH_SIZE = LOG_LAMBDA


DATA_SIZE = N*BALL_SIZE
OVERFLOW_SIZE = math.ceil(DATA_SIZE*EPSILON)
LOCAL_MEMORY_SIZE = BIN_SIZE_IN_BYTES
NUMBER_OF_BINS_IN_OVERFLOW = math.ceil(EPSILON*N/MU)

DATA_LOCATION = '17Mb.txt'
BINS_LOCATION = 'bins.txt'
OVERFLOW_LOCATION = 'overflow.txt'
# This is for the oblivious balls into bins so that the bins would not be overriden.
OVERFLOW_SECOND_LOCATION = 'second_overflow.txt'

BALL_READ = 0
BALL_WRITE = 0
RT_READ = 0
RT_WRITE = 0


MAIN_KEY = b'Sixteen byte key'
CUCKOO_HASH_KEY_1 = b'Cuckoo hash key1'
CUCKOO_HASH_KEY_2 = b'Cuckoo hash key2'


BALL_STATUS_POSITION = 4
DATA_STATUS = '\x01'
DUMMY_STATUS = '\x00'
# logn = 20
# n = 2**logn
# logLamb = 9
# lamb = 2**logLamb
# mu = 30*logLamb**3
# B = n/mu
# epsilon = 1/logLamb