from config import EPSILON, N, NUMBER_OF_BINS
import numpy as np

class ThresholdGenerator:
    def __init__(self) -> None:
        self.reset()
        pass
    
    def reset(self):
        self.b = NUMBER_OF_BINS
        self.nPrime = N - int(N*EPSILON)
    
    def generate(self):
        sample = np.random.binomial(self.nPrime, 1/self.b)
        self.b -= 1
        self.nPrime -= sample
        return sample