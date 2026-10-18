"""Reconstruct an immutable captured frame through NFPCSourceAPI (no emulator)."""
from pathlib import Path
import ctypes as C,hashlib,json
P=C.c_void_p;S=C.c_size_t;U=C.c_uint;Q=C.c_uint64
class API(C.Structure):_fields_=[('size',S),('core',P),('info',P),('background',P),('geometry',P),('road',P),('wall',P),('proof',P),('owner_thread',Q)]
def function(d,name,args,result=C.c_int):f=getattr(d,name);f.argtypes=args;f.restype=result;return f

def capture_witness(library,folder,metadata):
 folder=Path(folder);blobs={};owners={}
 for row in json.loads((folder/'witness-components.json').read_text()):
  data=(folder/Path(row['file']).name).read_bytes();assert len(data)==row['bytes'] and hashlib.sha256(data).hexdigest()==row['sha256'];blobs[row['owner'],row['kind']]=data;owners[row['owner']]=row['owner_info']
 Info=C.CFUNCTYPE(C.c_int,P,P);Background=C.CFUNCTYPE(S,P,Q,U,P,S);Read=C.CFUNCTYPE(S,P,Q,U,U,U,P,S)
 @Info
 def info(core,out):
  words=(Q*5)(metadata[0],metadata[1],0,0,0);C.memmove(out,words,40);return 1
 def copy(data,out,capacity):
  if not out:return len(data)
  if capacity<len(data):return 0
  C.memmove(out,data,len(data));return len(data)
 @Background
 def background(core,epoch,refresh,out,capacity):return copy(blobs[0,0],out,capacity) if [epoch,refresh]==metadata[:2] else 0
 callbacks=[]
 for kind in range(1,5):
  def read(core,epoch,serial,begin,end,out,capacity,kind=kind):
   for owner,identity in owners.items():
    if [epoch,serial,begin,end]==identity[:4]:return copy(blobs[owner,kind],out,capacity)
   return 0
  callbacks.append(Read(read))
 api=API(C.sizeof(API),1,C.cast(info,P),C.cast(background,P),*[C.cast(f,P) for f in callbacks],0);assert function(library,'nf_pc_source_api_bind_owner',[P])(C.byref(api))
 frame=function(library,'nf_pc_source_frame_capture',[P,S],P)(C.byref(api),64*1024*1024);assert frame
 actual=(Q*8)();assert function(library,'nf_pc_source_frame_info',[P,P])(frame,actual) and list(actual)==metadata
 return frame
