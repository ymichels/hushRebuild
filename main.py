
from config import STATIC_MEMORY_END_POSITION
from rebuild import Rebuild


Rebuild((0, STATIC_MEMORY_END_POSITION),
        STATIC_MEMORY_END_POSITION).ballsIntoBins()
