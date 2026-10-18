"""Exact original external-object rotation from closed builder provenance."""
import struct
from owned_scenery_projection import signed,multiply

from functools import lru_cache

def external_model_matrix(builder):
 return _external_model_matrix(builder.source,builder.camera,builder.initial_matrix,builder.external_enabled,builder.external_matrix)

@lru_cache(maxsize=256)
def _external_model_matrix(source,camera,initial_matrix,external_enabled,external_matrix):
 if len(source)!=164 or len(camera)!=48 or len(initial_matrix)!=48:raise ValueError('Invalid external builder envelope')
 flags=struct.unpack_from('<H',source,10)[0]
 if not flags&32 or external_enabled is None or not external_enabled or external_matrix is None or len(external_matrix)!=36:raise ValueError('Missing active external matrix provenance')
 camera=struct.unpack('<12i',camera);px,py,pz=struct.unpack_from('<3i',source,12)
 x=signed((px>>8)+camera[9]);z=signed((pz>>8)+camera[11]);depth=signed(camera[2]*x+camera[8]*z)>>14
 if not flags&2 and depth>3500:return initial_matrix
 rotation=multiply(tuple(signed(v<<2) for v in struct.unpack('<9i',external_matrix)),camera[:9])
 translation=(signed(camera[0]*x+camera[6]*z)>>14,signed((py>>8)+camera[10]),depth)
 return struct.pack('<12i',*(rotation+translation))
