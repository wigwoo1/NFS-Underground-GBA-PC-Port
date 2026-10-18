import ctypes as C
from pathlib import Path
class Event(C.Structure):
 _fields_=[('kind',C.c_uint),('count',C.c_uint),('shift',C.c_uint),('address',C.c_uint),('commands',C.c_void_p),('texture',C.c_void_p),('texture_size',C.c_size_t),('read',C.c_void_p),('context',C.c_void_p)]
lib=C.CDLL(str(Path('work/camera/native_scene_executor.dll').resolve()))
execute=lib.nf_scene_execute
execute.argtypes=[C.POINTER(Event),C.c_uint,C.c_void_p,C.c_size_t,C.c_void_p]
def run(kind,commands,count,vram,size,shift=0,address=0,texture=None,texture_size=0,read=None,context=None,writes=None):
 owned=C.create_string_buffer(texture) if isinstance(texture,bytes) else texture
 e=Event(kind,count,shift,address,C.cast(commands,C.c_void_p),C.cast(owned,C.c_void_p) if owned is not None else None,texture_size,C.cast(read,C.c_void_p) if read else None,context)
 if active is not None and C.cast(vram,C.c_void_p).value==active.address:
  if kind==1:
   if active.rom is None:
    raw=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes()
    active.rom=C.create_string_buffer(raw);active.rom_size=len(raw)
   e.address=0x08000000;e.texture=C.cast(active.rom,C.c_void_p);e.texture_size=active.rom_size;e.read=None;e.context=None
  if not lib.nf_scene_submit_stats(active.handle,C.byref(e),1,writes):return 0
  generation=C.c_uint64()
  assert lib.nf_scene_snapshot(active.handle,vram,0x18000,C.byref(generation))
  active.generation=generation.value
  return 1
 return execute(C.byref(e),1,vram,size,writes)
def road(commands,count,read,context,vram,size):return run(1,commands,count,vram,size,read=read,context=context)
def wall(commands,count,address,texture,texture_size,vram,size,writes):return run(2,commands,count,vram,size,address=address,texture=texture,texture_size=texture_size,writes=writes)
def model(commands,count,shift,address,texture,texture_size,vram,size):return run(3,commands,count,vram,size,shift=shift,address=address,texture=texture,texture_size=texture_size)

def fill(vram,size,offset,value,bytes):
 if size<0x18000:return 0
 commands=(C.c_uint32*3)(offset,value,bytes)
 return run(4,commands,1,vram,0x18000)
def copy(vram,size,offset,source,source_size,width,rows,ss,ds):
 if size<0x18000:return 0
 commands=(C.c_uint32*5)(offset,width,rows,ss,ds)
 return run(5,commands,1,vram,0x18000,texture=source,texture_size=source_size)
def block_copy(vram,size,offset,source,source_size,bytes):
 if size<0x18000:return 0
 commands=(C.c_uint32*2)(offset,bytes)
 return run(6,commands,1,vram,0x18000,texture=source,texture_size=source_size)

lib.nf_scene_create.argtypes=[C.c_void_p,C.c_size_t];lib.nf_scene_create.restype=C.c_void_p
lib.nf_scene_destroy.argtypes=[C.c_void_p]
lib.nf_scene_submit_stats.argtypes=[C.c_void_p,C.POINTER(Event),C.c_uint,C.c_void_p]
lib.nf_scene_snapshot.argtypes=[C.c_void_p,C.c_void_p,C.c_size_t,C.POINTER(C.c_uint64)]
active=None
class PersistentScene:
 def __init__(self,buffer):
  self.buffer=buffer;view=(C.c_uint8*len(buffer)).from_buffer(buffer)
  self.address=C.addressof(view);self.handle=lib.nf_scene_create(view,0x18000)
  assert self.handle
  self.generation=0;self.rom=None;self.rom_size=0
 def close(self):
  global active
  if self.handle:lib.nf_scene_destroy(self.handle);self.handle=None
  if active is self:active=None
def bind(buffer):
 global active
 assert active is None
 active=PersistentScene(buffer)
 return active

lib.nf_scene_fork.argtypes=[C.c_void_p];lib.nf_scene_fork.restype=C.c_void_p
def closing_snapshot(scene,operations):
 branch=lib.nf_scene_fork(scene.handle);assert branch
 commands=[];sources=[];events=[]
 try:
  for offset,source,size in operations:
   command=(C.c_uint32*2)(offset,size);owned=C.create_string_buffer(source)
   commands.append(command);sources.append(owned)
   events.append(Event(6,1,0,0,C.cast(command,C.c_void_p),C.cast(owned,C.c_void_p),len(source),None,None))
  batch=(Event*len(events))(*events)
  assert lib.nf_scene_submit_stats(branch,batch,len(events),None)
  result=(C.c_uint8*0x18000)();generation=C.c_uint64()
  assert lib.nf_scene_snapshot(branch,result,len(result),C.byref(generation))
  assert generation.value==scene.generation+1
  return bytes(result)
 finally:lib.nf_scene_destroy(branch)
