import random
import string


def get_random_string(length, BALL_STATUS_POSITION=None, status=None):
    # With combination of lower and upper case
    result_str = ''.join(random.choice(string.printable) for i in range(length))
    if status is not None:
        str_list = list(result_str)
        str_list[BALL_STATUS_POSITION] = status
        result_str = ''.join(str_list)
        
    # return random string
    return bytes(result_str,'utf-8')
