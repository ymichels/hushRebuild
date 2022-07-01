N = 2**20

BALL_SIZE = 16
MU = 30*9**3
NUMBER_OF_BINS = int(N/MU)
BIN_SIZE = 2*MU
BIN_SIZE_IN_BYTES = BIN_SIZE*BALL_SIZE
EPSILON = 1/9

DATA_SIZE = N*BALL_SIZE
LOCAL_MEMORY_SIZE = BIN_SIZE_IN_BYTES

DATA_LOCATION = '17Mb.txt'
BINS_LOCATION = 'bins.txt'
OVERFLOW_LOCATION = 'overflow.txt'

BALL_READ = 0
BALL_WRITE = 0
RT_READ = 0
RT_WRITE = 0
# logn = 20
# n = 2**logn
# logLamb = 9
# lamb = 2**logLamb
# mu = 30*logLamb**3
# B = n/mu
# epsilon = 1/logLamb