import hashlib,json
from pathlib import Path
from owned_native_frame_join_types_candidate import join_frame,span_array_type
owners=[]
for i in range(100):
 header=i.to_bytes(4,'little');geometry=(bytes([i])*128,b'geometry');base=b'prefix'+bytes([255-i])*4096
 expected=b''.join((header,*geometry,memoryview(base)[6:]));output=join_frame(header,geometry,base,6);assert output==expected;owners.append((output,hashlib.sha256(expected).hexdigest()))
assert all(hashlib.sha256(output).hexdigest()==digest for output,digest in owners)
assert span_array_type(4) is span_array_type(4)
for count in (0,4097,-1,1.5):
 try:span_array_type(count)
 except ValueError:pass
 else:raise AssertionError(count)
for count in range(1,100):span_array_type(count)
assert span_array_type.cache_info().currsize==64
out=dict(result='PASS_NATIVE_JOIN_TYPES_PRIVATE_OWNERS',private_outputs=100,bounded_type_cache=64,scope='Native copies exact and outputs survive subsequent calls; no live throughput claim')
Path('work/camera/prototype-runs/native-join-types-owners-20261008.json').write_text(json.dumps(out,indent=2));print(out)
