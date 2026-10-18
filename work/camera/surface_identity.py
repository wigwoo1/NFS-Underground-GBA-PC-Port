"""Stable world identities must not depend on the selected animation texture."""
import struct
def wall_identity(event):
 if event['pc']!=0x03000304:raise ValueError('Expected wall entry')
 b=event['blocks'];source=b[5][1]
 return ('wall',b[1][0],b[5][0],struct.unpack_from('<H',source,44)[0])
