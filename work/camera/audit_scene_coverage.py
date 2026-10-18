"""Bounded live capture coverage, with uncaptured runs as memory controls."""
from pathlib import Path
import ctypes as C, hashlib, json, struct
from collections import Counter, deque

root=Path('work').resolve();out=root/'camera'
d=C.CDLL(str(root/'nfsprobe.dll'))
Sink=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_uint64,C.c_void_p,C.c_size_t)
d.nf_init.argtypes=[C.c_char_p,C.c_char_p];d.nf_state.argtypes=[C.c_char_p,C.c_int]
d.nf_native_scene_sink.argtypes=[Sink,C.c_void_p]
d.nf_dump.argtypes=[C.c_char_p,C.c_uint32,C.c_uint32]
rom=b'G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba'
reports=[]
for name,steer in [('straight',0),('left',32),('right',16)]:
 hashes=[];packets=[];errors=[];last=deque(maxlen=2);spans=Counter();surfaces=Counter();gaps=[];identities=set()
 @Sink
 def receive(context,epoch,ptr,size):
  try:
   data=C.string_at(ptr,size)
   magic,version,total,count,serial,begin,end,page=struct.unpack_from('<8I',data)
   assert (magic,version,total,count)==(0x3150534e,1,size,5)
   sections={tag:data[offset:offset+length] for tag,offset,length in (struct.unpack_from('<3I',data,32+i*12) for i in range(5))}
   n=struct.unpack_from('<I',sections[5],4)[0]
   ids=[struct.unpack_from('<5I',sections[5],8+i*20) for i in range(n)]
   kinds=Counter(i[0] for i in ids);assert kinds[3]==1 and sum(kinds.values())==n
   order=struct.unpack_from('<'+'I'*n,sections[3],8)
   assert sorted(order)==list(range(n-1))+[0xffffffff]
   if packets and packets[-1][0]==epoch:
    if serial!=packets[-1][1]+1 or begin!=packets[-1][3]:gaps.append([packets[-1][1],serial,packets[-1][3],begin])
   packets.append((epoch,serial,begin,end,size));spans[end-begin]+=1;surfaces.update(kinds);identities.update(ids)
   last.append(data);return 1
  except Exception as error:errors.append(repr(error));return 0
 for enabled in (False,True):
  assert d.nf_init(rom,b'') and d.nf_state(str(root/'driving.state').encode(),0)
  try:
   if enabled:assert d.nf_native_scene_sink(receive,None)
   for frame in range(900):
    # Same steering schedule in the baseline and capture run.
    d.nf_frame(1 | (steer if 180<=frame<720 else 0))
   memory={}
   for region,address,size in [('ewram',0x02000000,0x40000),('iwram',0x03000000,0x8000),('vram',0x06000000,0x18000)]:
    path=out/f'coverage-{name}-{region}.bin';d.nf_dump(str(path).encode(),address,size)
    memory[region]=hashlib.sha256(path.read_bytes()).hexdigest()
   hashes.append(memory)
   if enabled:
    stats=(C.c_uint32*4)();d.nf_native_scene_stats(stats)
  finally:d.nf_close()
 assert hashes[0]==hashes[1],name
 assert not errors,errors
 assert stats[1]==len(packets) and stats[2]==stats[3]==0,(name,list(stats))
 assert not gaps,(name,gaps)
 for i,data in enumerate(last):(out/f'coverage-{name}-{i}.packet').write_bytes(data)
 report=dict(case=name,original_refreshes=900,memory_equal=True,hashes=hashes[0],published=len(packets),
             stats=dict(zip(('closed_current_epoch','published','rejected','sink_failures'),stats)),
             scene_span_histogram=dict(spans),surface_occurrences=dict(surfaces),unique_surface_identities=len(identities),
             serial_or_boundary_gaps=gaps,max_packet_bytes=max((p[4] for p in packets),default=0),
             epochs=len(set(p[0] for p in packets)))
 reports.append(report);print(json.dumps(report),flush=True)
result=dict(result='PASS',cases=reports,scope='Packet structure and capture noninterference under scripted steering. No proof that packets include every visible game object, or of displayed smoothness.')
(out/'scene-coverage-tests.json').write_text(json.dumps(result,indent=2))
