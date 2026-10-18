import struct,json,threading
from types import SimpleNamespace
from owned_spatial_decode_cache_candidate import SpatialDescriptors,_original,install,_local
install()
g=SimpleNamespace(geometry=struct.pack('<4I',7,1,0,0)+bytes(48)+bytes(68),offsets=bytes(32))
a=SpatialDescriptors(g);b=SpatialDescriptors(g);assert a.rows==b.rows and a.rows is not b.rows
a.rows.clear();assert SpatialDescriptors(g).rows==b.rows
changed=SimpleNamespace(geometry=g.geometry,offsets=b'X'+g.offsets[1:]);assert SpatialDescriptors(changed).rows[7][2][0]==88
held=b.rows.copy()
for i in range(8):SpatialDescriptors(SimpleNamespace(geometry=bytes(bytearray(g.geometry)),offsets=bytes(bytearray(g.offsets))))
assert b.rows==held and len(_local.entries)<=4
bad=SimpleNamespace(geometry=b'x',offsets=b'');errors=[]
for init in (_original,SpatialDescriptors.__init__):
 try:init(object.__new__(SpatialDescriptors),bad)
 except Exception as e:errors.append((type(e).__name__,str(e)))
assert len(errors)==2 and errors[0]==errors[1]
print(json.dumps(dict(result='PASS_PRIVATE_ROWS_IDENTITY_EVICTION_ERROR_PARITY',capacity=len(_local.entries))))
