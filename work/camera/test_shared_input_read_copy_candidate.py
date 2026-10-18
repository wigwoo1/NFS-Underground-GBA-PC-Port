from pathlib import Path
import sys,json
sys.path.insert(0,str(Path('work/camera').resolve()))
from multiprocessing.shared_memory import SharedMemory
from owned_shared_input_read_copy_candidate import copy_private
rows=[]
for size in (1,17,830071,8711745):
 memory=SharedMemory(create=True,size=size)
 try:
  expected=(bytes(range(256))*((size+255)//256))[:size];memory.buf[:size]=expected
  actual=copy_private(memory,size);assert type(actual)is bytes and actual==expected
  memory.buf[:size]=b'Z'*size;assert actual==expected
  for bad in (0,-1,size+1,True):
   try:copy_private(memory,bad)
   except ValueError:pass
   else:raise AssertionError('invalid extent accepted')
  rows.append(dict(size=size,exact=True,detached_after_source_overwrite=True))
 finally:memory.close();memory.unlink()
out=dict(result='PASS_NATIVE_PRIVATE_INPUT_COPY',rows=rows,scope='Exact immutable private bytes and mapping export cleanup; no live cadence proof.')
Path('outputs/nfsug-native-renderer/camera-research/native-private-input-copy-20261009.json').write_text(json.dumps(out,indent=2));print(out['result'])
