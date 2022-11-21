

import math
from config import baseConfig


class config(baseConfig):


    def __init__(self, N, is_map=False):
        self.N = N
        self.Z = 4
        self.KEY_SIZE = math.ceil(math.ceil(math.log(N,2))/8)
        if not is_map:
            self.BALL_DATA_SIZE = 4
            # the balls structure:  KEY || LEAF || DATA
            self.BALL_SIZE = 2*self.KEY_SIZE + self.BALL_DATA_SIZE
        else:
            raise "not implemented yet"
        
        self.LOCAL_MEMORY_SIZE_IN_BALLS = 2*30*(9**3)
        self.LOCAL_MEMORY_SIZE = self.LOCAL_MEMORY_SIZE_IN_BALLS*self.BALL_SIZE
        self.DATA_SIZE = N*self.BALL_SIZE*2*self.Z
        self.BUCKET_SIZE = self.Z*self.BALL_SIZE