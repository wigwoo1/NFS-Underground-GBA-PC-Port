"""Provisional endpoint road span candidates; actual source-run submission pending."""
import ctypes as C,struct,os,time
from owned_thread_cycles import read as thread_cycles
from pathlib import Path
import threading
_probe_path=str(Path(__file__).with_name('visibility-probe-wide.dll').resolve())
_road_table_local=threading.local()
def _native_reciprocal(values):
 if len(values)!=32768:raise ValueError('Invalid road reciprocal size')
 if isinstance(values,tuple):
  cached=getattr(_road_table_local,'table',None)
  if cached is not None and cached[0] is values:return cached[1]
 table=(C.c_uint32*32768)(*values)
 if isinstance(values,tuple):_road_table_local.table=(values,table)
 return table
from owned_wall_region_candidates import regions
_library_local=threading.local()
def road_library():
 d=getattr(_library_local,'library',None)
 if d is None:d=C.CDLL(_probe_path);_library_local.library=d
 return d
ClipPoints=C.c_int32*(128*6)
Framebuffer=C.c_uint32*4
Spans=C.c_uint32*(512*4)

Reader=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_uint32,C.c_void_p,C.c_size_t)
def endpoint_road_span_candidates(closed,memory,candidates,reciprocal,*,include_empty=False,trace=None):
 read_counts=[0,0]
 def begin():return (time.perf_counter_ns(),thread_cycles(),tuple(read_counts)) if trace is not None else None
 def finish(name,descriptor,start):
  if start is None:return
  now=time.perf_counter_ns();cycles=thread_cycles()
  if len(trace)<512:trace.append(dict(name=name,descriptor=descriptor,started_ns=start[0],completed_ns=now,wall_ns=now-start[0],thread_cycles=cycles-start[1],python_memory_reads=read_counts[0]-start[2][0],python_memory_bytes=read_counts[1]-start[2][1]))
 d=road_library();table=_native_reciprocal(reciprocal)
 d.nfs_visibility_region_reconstruct.argtypes=[C.c_void_p,C.c_void_p,Reader,C.c_void_p,C.c_void_p,C.c_void_p,C.c_size_t,C.c_void_p,C.c_size_t]
 d.nf_road_polygon_clip.argtypes=[C.c_void_p,C.c_uint,C.c_int32,C.c_int32,C.c_void_p,C.c_void_p,C.c_uint,C.c_void_p]
 d.nf_road_span_plan.argtypes=[C.c_void_p,C.c_uint,C.c_int32,C.c_int32,C.c_uint,C.c_uint,C.c_void_p,C.c_void_p,C.c_void_p,C.c_uint,C.c_void_p]
 @Reader
 def read(ctx,address,out,size):
  read_counts[0]+=1;read_counts[1]+=size
  try:C.memmove(out,memory.read(address,size),size);return 1
  except ValueError:return 0
 context=None;native_reader=None
 if os.environ.get('NF_NATIVE_ROAD_READER')=='1':
  from owned_native_sparse_reader import reader_for_memory
  native_reader=reader_for_memory(memory,Reader);read=native_reader.callback;context=native_reader.pointer
 result=[]
 def visit(ordinal,region,stack=()):
  identifier=region[0]
  if identifier in stack or len(stack)>=512:raise ValueError('Cyclic static road traversal')
  descriptor=memory.read(struct.unpack_from('<I',closed.graph.context,20)[0]+identifier*48,48)
  if descriptor[18]&8:raise ValueError('Recursive road surface requires sibling executor')
  state=C.create_string_buffer(closed.graph.context[:256],256);edges=C.create_string_buffer(32*52);stream=C.create_string_buffer(64*24)
  record=struct.pack('<8H',*region,65535) if len(region)==7 else struct.pack('<8H',*region)
  started=begin()
  status=d.nfs_visibility_region_reconstruct(state,record,read,context,table,edges,len(edges),stream,len(stream))
  finish('region_reconstruct',identifier,started)
  if status<0:raise ValueError('Unowned road reconstruction')
  if not status:return
  yield ordinal,region,state,stream,len(stack)
  child=struct.unpack_from('<H',descriptor,6)[0]
  if child!=65535:
   if child>=512:raise ValueError('Invalid static road child')
   yield from visit(ordinal,(child,*region[1:]),stack+(identifier,))
 visits=(item for ordinal,region in reversed(list(enumerate(regions(closed.graph,reciprocal)))) if not region[5]&8 for item in visit(ordinal,region))
 try:
  for ordinal,region,state,stream,depth in visits:
   sources=[x for x in candidates if x.descriptor==region[0]]
   if not sources:continue
   count=struct.unpack_from('<H',state.raw,242)[0];clipped=ClipPoints();amount=C.c_uint()
   started=begin()
   if not d.nf_road_polygon_clip(stream,count,region[1],region[2],table,clipped,128,C.byref(amount)):raise ValueError('Road horizontal clipping failed')
   finish('polygon_clip',region[0],started)
   framebuffer=Framebuffer.from_buffer_copy(closed.graph.context[304:320])
   for source in sorted(sources,key=lambda x:x.secondary):
    points=ClipPoints();C.memmove(points,clipped,C.sizeof(clipped))
    if source.secondary:
     for i in range(amount.value):points[i*6+1]=points[i*6+2]
    spans=Spans();n=C.c_uint();orientation=source.descriptor_bytes[18]&(2 if source.secondary else 1)
    started=begin()
    if not d.nf_road_span_plan(points,amount.value,region[3],region[4],orientation,region[5]&1,table,framebuffer,spans,512,C.byref(n)):raise ValueError('Road span selection failed')
    finish('span_plan',source.descriptor,started)
    if include_empty or (n.value and any(spans[i*4+1] for i in range(n.value))):result.append(dict(ordinal=ordinal,static_depth=depth,descriptor=source.descriptor,secondary=source.secondary,bounds=region[1:5],source=source,spans=n.value,input_count=count,affine=region[5]&1,orientation=orientation))
 finally:
  visits.close()
  visit=None
 return tuple(result)

