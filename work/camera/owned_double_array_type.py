"""Bounded type reuse; each caller still allocates a private array."""
import ctypes as C
from functools import lru_cache

@lru_cache(maxsize=256)
def double_array_type(length):
 if type(length) is not int or length<0:raise ValueError("Invalid double array length")
 return C.c_double*length
