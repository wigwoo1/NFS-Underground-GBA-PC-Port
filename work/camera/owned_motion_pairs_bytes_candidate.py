"""Source-identity pairing for owned scene motion; no screen coordinates."""
import struct,hashlib,threading,time
from owned_thread_cycles import read as thread_cycles
from collections import Counter
from owned_motion_pairs import _decode_records as mutable_decode
from owned_segmented_frame_candidate import SegmentedFrame

def _decode_records(frame,source_keys=True):
 if type(frame) is not bytes and not isinstance(frame,SegmentedFrame):
  return mutable_decode(frame,source_keys)
 if len(frame)<40:raise ValueError('Truncated owned frame')
 buffer=frame.prefix if isinstance(frame,SegmentedFrame) else frame
 magic,refresh,gn,hn,bn,tn,epoch,ticks=struct.unpack_from('<6I2Q',buffer)
 if magic!=0x3346474e or not epoch or ticks!=refresh*280896 or gn+hn+bn+tn+40!=len(frame):raise ValueError('Invalid owned frame envelope')
 g=memoryview(buffer)[40:40+gn];out=[];offset=0
 while offset<len(g):
  if len(g)-offset<16:raise ValueError('Truncated source header')
  magic,kind,context,count=struct.unpack_from('<4I',g,offset);offset+=16
  if magic!=0x3147534e or kind not in (1,2,3) or count!=12:raise ValueError('Invalid source kind')
  blocks=[]
  for _ in range(count):
   if len(g)-offset<4:raise ValueError('Truncated source length')
   n=struct.unpack_from('<I',g,offset)[0];offset+=4
   if n>0x100000 or n>len(g)-offset:raise ValueError('Invalid source block')
   blocks.append(bytes(g[offset:offset+n]));offset+=n
  # Static raw topology supplies identity; textures, poses and clipping remain discrete payload.
  ids=(0,1,2,9) if kind==1 else (0,1,7) if kind==2 else (1,4,5,6,7,8)
  key=None
  if source_keys:
   h=hashlib.sha256()
   for i in ids:h.update(struct.pack('<I',len(blocks[i])));h.update(blocks[i])
   key=(kind,context,h.hexdigest())
  out.append(dict(kind=kind,context=context,blocks=blocks,key=key))
 return dict(refresh=refresh,epoch=epoch,ticks=ticks,records=out)

_record_cache=threading.local()
def records(frame,trace=None):
 def mark(name,**details):
  nonlocal started,cycles
  now=time.perf_counter_ns();current=thread_cycles()
  trace.append(dict(name=name,started_ns=started,completed_ns=now,wall_ns=now-started,thread_cycles=current-cycles,**details));started=now;cycles=current
 if trace is not None:started=time.perf_counter_ns();cycles=thread_cycles()
 if type(frame) is not bytes and not isinstance(frame,SegmentedFrame):
  result=_decode_records(frame)
  if trace is not None:mark('mutable_decode',records=len(result['records']),frame_bytes=len(frame))
  return result
 entries=getattr(_record_cache,'entries',[])
 for owner,header,rows in entries:
  if owner is frame:break
 else:
  if trace is not None:mark('cache_lookup',hit=False,entries=len(entries))
  result=_decode_records(frame)
  if trace is not None:mark('uncached_decode',records=len(result['records']),frame_bytes=len(frame),refresh=result['refresh'])
  header=(result['refresh'],result['epoch'],result['ticks'])
  rows=tuple((r['kind'],r['context'],tuple(r['blocks']),r['key']) for r in result['records'])
  if trace is not None:mark('cache_metadata_pack')
  entries.append((frame,header,rows));_record_cache.entries=entries[-4:]
  # Release previous cache-list ownership within the measured stage.
  del entries
  if trace is not None:mark('cache_replace')
  result=dict(refresh=header[0],epoch=header[1],ticks=header[2],records=[dict(kind=k,context=c,blocks=list(b),key=key) for k,c,b,key in rows])
  if trace is not None:mark('caller_containers')
  return result
 if trace is not None:mark('cache_lookup',hit=True,entries=len(entries))
 result=dict(refresh=header[0],epoch=header[1],ticks=header[2],records=[dict(kind=k,context=c,blocks=list(b),key=key) for k,c,b,key in rows])
 if trace is not None:mark('caller_containers')
 return result

def plan_pair(older,newer):
 a=records(older);b=records(newer)
 if a['epoch']!=b['epoch'] or a['ticks']>=b['ticks']:raise ValueError('Scene epoch/time cut')
 def camera(scene):
  mats=[bytes(r['blocks'][4 if r['kind']==1 else 3]) for r in scene['records'] if r['kind'] in (1,2)]
  if not mats or any(len(m)!=48 or m!=mats[0] for m in mats):raise ValueError('Missing or incoherent world camera')
  return mats[0]
 ca,cb=camera(a),camera(b)
 ac=Counter(r['key'] for r in a['records']);bc=Counter(r['key'] for r in b['records'])
 newer_index={r['key']:i for i,r in enumerate(b['records']) if bc[r['key']]==1}
 pairs=[];held=[]
 for i,r in enumerate(a['records']):
  key=r['key']
  if ac[key]==1 and bc[key]==1:pairs.append((i,newer_index[key]))
  else:held.append(dict(index=i,reason='ambiguous source identity' if ac[key]>1 or bc[key]>1 else 'source topology or visibility changed'))
 paired_new={j for i,j in pairs}
 return dict(older=a,newer=b,camera_older=ca,camera_newer=cb,pairs=pairs,held=held,births=[i for i in range(len(b['records'])) if i not in paired_new])

