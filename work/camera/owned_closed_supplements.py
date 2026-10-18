"""Immutable supplemental sections paired with the atomic closed graph."""
from dataclasses import dataclass
import struct,os,time,threading
_trace_local=threading.local()
def supplement_trace():return getattr(_trace_local,"last",None)
from owned_scene_bundle import chunks
from owned_thread_cycles import read as _thread_cycles
@dataclass(frozen=True)
class ClosedSupplements:
 epoch:int
 refresh:int
 source_refresh:int
 geometry:bytes
 textures:bytes
 @classmethod
 def decode(cls,encoded,graph,rom=None):
  trace=None
  if os.environ.get('NFSUG_SUPPLEMENT_FINE_TRACE')=='1':
   _trace_local.last=None
   if int(os.environ.get('NFSUG_SUPPLEMENT_FINE_FIRST','0'))<=graph.refresh<=int(os.environ.get('NFSUG_SUPPLEMENT_FINE_LAST','4294967295')):
    trace=[];started=time.perf_counter_ns();started_cpu=time.thread_time_ns();started_cycles=_thread_cycles()
  def mark(name):
   nonlocal started,started_cpu,started_cycles
   if trace is not None:
    now=time.perf_counter_ns();cpu=time.thread_time_ns();cycles=_thread_cycles();trace.append(dict(name=name,started_ns=started,completed_ns=now,wall_ns=now-started,thread_cpu_ns=cpu-started_cpu,thread_cycles=cycles-started_cycles));started=now;started_cpu=cpu;started_cycles=cycles
  raw=bytes(encoded)
  if len(raw)<32 or len(raw)>16*1024*1024:raise ValueError('Invalid closed supplemental size')
  h=struct.unpack_from('<6I',raw);epoch=struct.unpack_from('<Q',raw,24)[0]
  if h[:2]!=(0x3143534e,1) or epoch!=graph.epoch or h[2]!=graph.refresh or h[3]!=graph.graph.refresh or sum(h[4:])+32!=len(raw):raise ValueError('Unpaired closed supplemental packet')
  geometry=raw[32:32+h[4]];textures=raw[32+h[4]:];expected=set();seen=set();camera=graph.graph.context[256:304]
  mark('header_sections')
  for gh,data in chunks(geometry,'supplements'):
   if gh[0]!=0x3147534e or gh[6]!=1 or not h[3]<=gh[1]<=h[2] or not 0<gh[4]<=32 or gh[5]!=944+gh[4]*140 or data[80:128]!=camera:raise ValueError('Invalid supplemental geometry')
   for edge in range(gh[4]):
    key=(gh[1],gh[2],gh[3],edge)
    if key in expected:raise ValueError('Duplicate supplemental geometry')
    expected.add(key)
  mark('geometry_validation')
  from owned_supplemental_dependencies import dependencies
  owned_descriptors={d.descriptor for d in dependencies(graph)}
  mark('owned_dependencies')
  owned_states={header[2] for header,_ in chunks(graph.objects,'graph_objects')}
  mark('owned_states')
  source_edges=None
  if rom is not None:
   from owned_supplemental_rom_geometry import recover_geometry
   source_edges={(asset.descriptor,edge):mi for asset in recover_geometry(graph,rom).values() for edge,mi in enumerate(asset.material_indices)}
  mark('rom_source_edges')
  seen_edges=set()
  for _,data in chunks(textures,'textures'):
   th=struct.unpack_from('<12I',data);key=tuple(th[1:5])
   if th[0]!=0x3154534e or th[11]!=1 or (key not in expected and not (th[1]==h[3] and th[3] in owned_descriptors and th[4]<32)) or key in seen or th[7]>10 or not 0<th[8]<=1024 or th[10]!=(1<<th[7])*th[8] or th[10]>65536:raise ValueError('Invalid supplemental texture ownership')
   if th[2] not in owned_states:raise ValueError('Unowned supplemental texture state')
   if source_edges is not None and source_edges.get((th[3],th[4]))!=th[5]:raise ValueError('Supplemental source edge material mismatch')
   seen.add(key);seen_edges.add((th[3],th[4]))
  mark('texture_validation')
  if {(key[2],key[3]) for key in expected}-seen_edges:raise ValueError('Incomplete supplemental textures')
  result=cls(epoch,h[2],h[3],geometry,textures)
  mark('complete')
  if trace is not None:_trace_local.last=dict(epoch=epoch,refresh=h[2],stages=trace,geometry_bytes=len(geometry),texture_bytes=len(textures))
  return result
