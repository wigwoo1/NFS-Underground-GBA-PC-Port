from pathlib import Path
import ctypes as C,csv,json,struct,hashlib
p=Path('work/camera').resolve();out=p.parents[1]/'outputs/nfsug-native-renderer/camera-research';audit=json.loads((out/'native-world-audit.json').read_text());prefix=p/'prototype-runs/threaded-923c5fa0b0c14d9292907cbf8e50cc13'
d=C.CDLL(str(p.parent/'nfsprobe.dll'));d.nf_init.argtypes=[C.c_char_p]*2;d.nf_state.argtypes=[C.c_char_p,C.c_int];d.nf_read.argtypes=[C.c_uint,C.c_int];d.nf_read.restype=C.c_uint
rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba');state=p.parent/'driving.state';hashes=[hashlib.sha256(f.read_bytes()).hexdigest() for f in (rom,state)]
assert d.nf_init(str(rom).encode(),b'') and d.nf_state(str(state).encode(),0)
def read(a,n):return bytes(d.nf_read(a+i,1)&255 for i in range(n))
def u32(b,o=0):return struct.unpack_from('<I',b,o)[0]
def i32(b,o=0):return struct.unpack_from('<i',b,o)[0]
def u16(b,o=0):return struct.unpack_from('<H',b,o)[0]
def i16(b,o=0):return struct.unpack_from('<h',b,o)[0]
results=[]
try:
 for row in csv.DictReader(Path(str(prefix)+'-input.csv').open()):
  d.nf_frame(int(row['keys']))
  if int(row['after'])==8881:break
 else:raise AssertionError('checkpoint absent')
 for item in audit['surfaces']:
  if item['index'] not in (10,11,12,13,25):continue
  st=read(int(item['state'],16),256);address=int(item['source'],16);src=read(address,68)
  table=read(u32(st,20),512*48);owners=[]
  for j in range(512):
   candidate=table[j*48:(j+1)*48];start=u32(st,16)+u16(candidate)*68;count=u16(candidate,2)
   if 0<count<=32 and start<=address and address+68<=start+count*68 and (address-start)%68==0:owners.append(candidate)
  if len(owners)!=1:
   results.append(dict(index=item['index'],source=item['source'],owner_matches=len(owners),geometry_unverified='Scene-end owner lookup ambiguous or absent; retained invocation required.'));continue
  owner=owners[0]
  base=u32(st,16)+u16(owner)*68;count=u16(owner,2);index=(address-base)//68
  if not (0<=index<count and (address-base)%68==0):
   results.append(dict(index=item["index"],source=item["source"],owner=item["base"],state_source_base=hex(u32(st,16)),derived_base=hex(base),owner_count=count,geometry_unverified="Scene-end mutable state does not contain this source/owner; invocation-time retained state required."));continue
  nxt=read(base+(index+1)%count*68,68)
  def offset(s):return bytes(32) if u16(s,42)==65535 else read(u32(st,24)+u16(s,42)*32,32)
  a=offset(src);b=offset(nxt)
  x=i32(src)+i16(a);z=i32(src,4)+i16(a,2);nx=i32(nxt)+i16(b);nz=i32(nxt,4)+i16(b,2)
  recovered=[[x,i16(src,8)+i16(a,8),z],[nx,i16(src,12)+i16(a,8),nz],[nx,i16(src,14)+i16(a,10),nz],[x,i16(src,10)+i16(a,10),z]]
  results.append(dict(index=item['index'],source=item['source'],owner=item['base'],flags=hex(u16(src,46)),source_heights=[i16(src,o) for o in (8,10,12,14)],offsets=[i16(a,o) for o in (0,2,8,10)],raw_recovered_vertices=recovered,packet_vertices=item['vertices'],exact_geometry_match=recovered==item['vertices'],source_hex=src.hex()))
finally:d.nf_close()
assert hashes==[hashlib.sha256(f.read_bytes()).hexdigest() for f in (rom,state)]
report=dict(result='AUDITED',refresh=8881,rom_state_unchanged=True,surfaces=results,scope='Original replay memory at scene-end refresh; raw source/owner/offset formula comparison. Not invocation-time retained memory or original pixel-column equivalence.')
(out/'native-wall-source-audit.json').write_text(json.dumps(report,indent=2));print(json.dumps([(r['index'],r.get('exact_geometry_match'),r.get('geometry_unverified')) for r in results]))
