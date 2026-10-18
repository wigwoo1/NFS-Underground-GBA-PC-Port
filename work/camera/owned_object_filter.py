"""Original ARM object depth and wrapped distance ordering from owned sources."""
import struct
def signed(value):
 value&=0xffffffff
 return value-0x100000000 if value&0x80000000 else value
def depth_distance(source,camera):
 if len(source)!=164 or len(camera)!=48:raise ValueError('Invalid owned source')
 m=struct.unpack('<12i',camera)
 x=struct.unpack_from('<i',source,12)[0]>>8;z=struct.unpack_from('<i',source,20)[0]>>8
 x=signed(m[9]+x);z=signed(m[11]+z)
 depth=signed(signed(m[8]*z)+signed(m[2]*x))>>14
 horizontal=signed(signed(m[6]*z)+signed(m[0]*x))>>14
 distance=signed(signed(depth*depth)+signed(horizontal*horizontal))>>8
 return depth,distance,horizontal
def ordered(candidates):
 # Original insertion uses >= at head and <= at interior, so ties reverse input order.
 out=[]
 for index,depth,distance in candidates:
  if depth<=0:continue
  position=0
  while position<len(out) and out[position][1]>distance:position+=1
  out.insert(position,(index,distance))
 return [index for index,_ in out]

def eligibility(source,visited=False):
 if len(source)!=164:raise ValueError('Invalid owned object')
 flags=struct.unpack_from('<H',source,8)[0]
 active=struct.unpack_from('<H',source,72)[0]
 if visited:return 'visited'
 if not active:return 'inactive'
 if flags&1 and not flags&2:return 'callback'
 return 'project' if flags&4 else 'hidden'

def select_owned(head,objects,camera,callback_sources=None,visited=None):
 """Walk original association links, select and order callback-complete owned objects."""
 seen=set() if visited is None else visited
 callbacks={} if callback_sources is None else callback_sources
 chain_seen=set();candidates=[]
 while head!=65535:
  if head in chain_seen or len(chain_seen)>=512:raise ValueError('Invalid association chain')
  chain_seen.add(head)
  if head not in objects:raise ValueError('Missing association object')
  source=objects[head];decision=eligibility(source,head in seen)
  if decision!='visited':seen.add(head)
  if decision=='callback':
   if head not in callbacks:raise ValueError('Missing callback-complete object')
   source=callbacks[head]
   if len(source)!=164:raise ValueError('Invalid callback object')
   decision='project' if struct.unpack_from('<H',source,8)[0]&4 else 'hidden'
  if decision=='project':
   depth,distance,_=depth_distance(source,camera);candidates.append((head,depth,distance))
  head=struct.unpack_from('<H',source,2)[0]
 return ordered(candidates)
