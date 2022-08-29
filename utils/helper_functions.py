import random
import string

def get_random_string(length):
    # With combination of lower and upper case
    result_str = ''.join(random.choice(string.printable) for i in range(length))
    # print random string
    return bytes(result_str,'utf-8')
