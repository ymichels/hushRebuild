import random
import string


def get_random_string(length, BALL_STATUS_POSITION=None, status=None):
    # With combination of lower and upper case
    result_str = ''.join(random.choice(string.printable) for i in range(length))
    if status is not None:
        result = bytes(result_str,'utf-8')
        return result[:BALL_STATUS_POSITION] + status + result[1 + BALL_STATUS_POSITION:]
        
    # return random string
    return bytes(result_str,'utf-8')


def uniqueAccross(list1,list2):
    list1 = unique(list1)
    list2 = unique(list2)
    new_list1 = []
    for item in list1:
        if item not in list2:
            new_list1.append(item)
    return new_list1, list2

def unique(list1):
    return list(set(list1))
