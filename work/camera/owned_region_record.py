"""Original region queue transport, including linked-parent word."""
import struct
def encode(region):
 if len(region)==7:region=(*region,65535)
 if len(region)!=8:raise ValueError('Invalid region word count')
 return struct.pack('<8H',*region)
