"""Typed raw byte sections with small trusted-process metadata; no whole blob copy."""
import struct,pickle,os
DEDUPLICATE_BYTES=os.environ.get("NF_SHARED_DEDUP_BYTES")=="1"
from dataclasses import dataclass
from multiprocessing.shared_memory import SharedMemory
from owned_shared_blob import _HEADER,_MAGIC
@dataclass(frozen=True)
class ByteReference:index:int

def parts(payload):
 blobs=[];unique={} if globals().get("DEDUPLICATE_BYTES",False) else None
 # Process tails are already unique from encode_samples; avoid hashing their multi-MB bytes again.
 def replace(x,allow_dedup=True):
  if isinstance(x,memoryview):
   if not x.readonly or not x.c_contiguous or type(x.obj) is not bytes or x.format!="B":raise ValueError("Shared span must retain contiguous immutable bytes")
   index=len(blobs);blobs.append(x);return ByteReference(index)
  if isinstance(x,bytes):
   if allow_dedup and unique is not None and x in unique:return ByteReference(unique[x])
   index=len(blobs);blobs.append(x)
   if allow_dedup and unique is not None:unique[x]=index
   return ByteReference(index)
  if isinstance(x,dict):return {k:replace(v,allow_dedup and k!="tails") for k,v in x.items()}
  if isinstance(x,list):return [replace(v,allow_dedup) for v in x]
  if isinstance(x,tuple):return tuple(replace(v,allow_dedup) for v in x)
  if x is None or isinstance(x,(str,int,float,bool)):return x
  raise ValueError('Unsupported shared metadata')
 metadata=pickle.dumps(replace(payload),protocol=5)
 if len(blobs)>512 or len(metadata)>1024*1024:raise ValueError('Shared metadata budget exceeded')
 return metadata,blobs

def write_payload(memory,payload,generation,serial):
 metadata,blobs=parts(payload);sizes=[len(x) for x in blobs]
 directory=struct.pack('<2I',len(metadata),len(blobs))+struct.pack('<'+'I'*len(sizes),*sizes)
 total=len(directory)+len(metadata)+sum(sizes)
 if total>min(64*1024*1024,memory.size-_HEADER.size):raise ValueError('Shared output budget exceeded')
 at=_HEADER.size
 for section in (directory,metadata,*blobs):memory.buf[at:at+len(section)]=section;at+=len(section)
 _HEADER.pack_into(memory.buf,0,_MAGIC,generation,serial,total)
 return memory.name,generation,serial,total

def read_payload(descriptor,generation,memory=None):
 name,actual,serial,length=descriptor
 if actual!=generation or not 0<serial or not 8<=length<=64*1024*1024:raise ValueError('Invalid shared payload identity')
 owned_memory=memory is None
 if owned_memory:memory=SharedMemory(name=name)
 elif memory.name!=name:raise ValueError("Shared mapping owner mismatch")
 try:
  expected=(_MAGIC,generation,serial,length)
  if length>memory.size-_HEADER.size or _HEADER.unpack_from(memory.buf)!=expected:raise ValueError('Stale shared payload')
  at=_HEADER.size;end=at+length;meta_size,count=struct.unpack_from('<2I',memory.buf,at);at+=8
  if count>512 or meta_size>1024*1024 or at+count*4+meta_size>end:raise ValueError('Invalid shared section directory')
  sizes=struct.unpack_from('<'+'I'*count,memory.buf,at);at+=count*4
  if at+meta_size+sum(sizes)!=end:raise ValueError('Invalid shared section lengths')
  metadata=pickle.loads(bytes(memory.buf[at:at+meta_size]));at+=meta_size;blobs=[]
  for size in sizes:blobs.append(bytes(memory.buf[at:at+size]));at+=size
  def restore(x):
   if isinstance(x,ByteReference):
    if not isinstance(x.index,int) or not 0<=x.index<len(blobs):raise ValueError('Invalid shared byte reference')
    return blobs[x.index]
   if isinstance(x,dict):return {k:restore(v) for k,v in x.items()}
   if isinstance(x,list):return [restore(v) for v in x]
   if isinstance(x,tuple):return tuple(restore(v) for v in x)
   if x is None or isinstance(x,(str,int,float,bool)):return x
   raise ValueError('Invalid shared metadata type')
  result=restore(metadata)
  if _HEADER.unpack_from(memory.buf)!=expected:raise ValueError('Changed shared payload')
  return result
 finally:
  if owned_memory:memory.close()
