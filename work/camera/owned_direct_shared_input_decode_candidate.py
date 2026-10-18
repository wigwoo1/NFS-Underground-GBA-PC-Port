"""Isolated synchronous decode under existing writer-held request lifetime."""
import pickle
def decode_private(memory,size):
 if type(size) is not int or not 0<size<=memory.size or size>64*1024*1024:raise ValueError('Invalid direct decode extent')
 view=memory.buf[:size]
 try:return pickle.loads(view)
 finally:view.release()
