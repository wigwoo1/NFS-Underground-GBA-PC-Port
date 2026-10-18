"""Complete prepared sample byte signatures for diagnostic parity."""
import hashlib

def signature(sample):
 return dict(buffers=[None if x is None else dict(bytes=len(bytes(x)),sha256=hashlib.sha256(bytes(x)).hexdigest()) for x in sample[:4]],detail=sample[4])
