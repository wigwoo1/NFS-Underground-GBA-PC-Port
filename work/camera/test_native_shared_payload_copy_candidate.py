from multiprocessing.shared_memory import SharedMemory
from pathlib import Path
import ctypes as C,json
from owned_shared_payload_copy_binding_candidate import copy_payload,library
memory=SharedMemory(create=True,size=64*1024*1024);sizes=[1,17,830071,8711745,64*1024*1024]
try:
 for size in sizes:
  payload=(bytes(range(256))*((size+255)//256))[:size];copy_payload(memory,payload);assert bytes(memory.buf[:size])==payload
 for bad in (b'',bytearray(b'1'),b'x'*(memory.size+1)):
  try:copy_payload(memory,bad);raise AssertionError('Invalid payload accepted')
  except ValueError:pass
 target=C.c_char.from_buffer(memory.buf);pointer=C.addressof(target)
 assert library.nf_shared_payload_copy(None,memory.size,C.c_char_p(b'x'),1)==37
 assert library.nf_shared_payload_copy(pointer,memory.size,pointer,1)==39
 assert library.nf_shared_payload_copy(pointer,1,C.c_char_p(b'xx'),2)==37
 del target
finally:memory.close();memory.unlink()
out=dict(result='PASS_EXACT_NATIVE_SHARED_COPY',exact_sizes=sizes,scope='Exact immutable payload bytes through maximum64MB, invalid bounds/types/null/overlap rejection and mapping close/unlink. CDLL releases GIL; no realtime cadence claim.')
Path('outputs/nfsug-native-renderer/camera-research/native-shared-copy-tests-20261009.json').write_text(json.dumps(out,indent=2));print(out['result'])
