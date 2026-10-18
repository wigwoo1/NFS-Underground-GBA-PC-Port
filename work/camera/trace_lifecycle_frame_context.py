"""Retained frontend context through original-input title transition and race."""
import ctypes as C,hashlib,json,struct
from pathlib import Path
p=Path(__file__).resolve().parent;out=p/'prototype-runs/lifecycle-context';rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba');raw=rom.read_bytes();P=C.c_void_p;Sink=C.CFUNCTYPE(C.c_int,P,C.c_uint64,P,C.c_size_t)
d=C.CDLL(str(p/'visibility-probe-wide.dll'));b=C.CDLL(str(p.parent/'nfsprobe.dll'))
for dll in (d,b):dll.nf_init.argtypes=[C.c_char_p]*2;dll.nf_state.argtypes=[C.c_char_p,C.c_int];dll.nf_read.argtypes=[C.c_uint,C.c_int];dll.nf_dump.argtypes=[C.c_char_p,C.c_uint,C.c_uint]
d.nf_native_scene_epoch.restype=C.c_uint64;d.nf_native_scene_sink.argtypes=[Sink,P];d.nf_layer_queue_context.argtypes=[C.c_uint64,C.c_uint,P]
@Sink
def sink(*args):return 1
checks=[]
for name,state,keys in [('title-start',p.parent/'fix-menu/menu-4.state',[0]*40+[8]*2+[0]*180),('race',p.parent/'driving.state',[1]*80)]:
 statehash=hashlib.sha256(state.read_bytes()).hexdigest();assert d.nf_init(str(rom).encode(),b'') and d.nf_state(str(state).encode(),0) and d.nf_native_scene_sink(sink,None) and d.nf_layer_queue_enable(1);history=[]
 try:
  for i,key in enumerate(keys):
   d.nf_frame(key);meta=(C.c_uint32*3)();found=d.nf_layer_queue_context(d.nf_native_scene_epoch(),d.nf_layer_queue_latest(),meta);history.append(dict(index=i,key=key,refresh=d.nf_layer_queue_latest(),captured=list(meta) if found else None,current=[d.nf_read(0x03005f14,4),d.nf_read(0x03006710,1)]))
  actual=[]
  for label,base,size in [('ewram',0x02000000,0x40000),('iwram',0x03000000,0x8000)]:
   path=out/(name+'-'+label+'.bin');d.nf_dump(str(path).encode(),base,size);actual.append(path.read_bytes())
 finally:d.nf_close()
 assert b.nf_init(str(rom).encode(),b'') and b.nf_state(str(state).encode(),0)
 try:
  for key in keys:b.nf_frame(key)
  for expected,(label,base,size) in zip(actual,[('ewram',0x02000000,0x40000),('iwram',0x03000000,0x8000)]):
   path=out/(name+'-baseline-'+label+'.bin');b.nf_dump(str(path).encode(),base,size);assert path.read_bytes()==expected
 finally:b.nf_close()
 assert hashlib.sha256(state.read_bytes()).hexdigest()==statehash
 if name=='race':assert all(h['captured'][0]==5 and h['captured'][2]==1 for h in history if h['captured']) and sum(bool(h['captured']) for h in history)>70
 checks.append(dict(name=name,exact_original_ram=True,state_sha256=statehash,history=history));print(name,sorted(set(tuple(h['captured']) for h in history if h['captured'])),flush=True)
report=dict(result='PASS',rom_sha256=hashlib.sha256(raw).hexdigest(),dispatch_pc='08001804',table_pointer=hex(struct.unpack_from('<I',raw,0x1820)[0]),selector_pointer=hex(struct.unpack_from('<I',raw,0x1824)[0]),handlers={str(i):hex(struct.unpack_from('<I',raw,0x653ae0+i*4)[0]) for i in [0,1,3,4,18]},checks=checks,scope='Original RAM-derived retained perrefresh scene context, neutral/race/Start original inputs, fullRAM baseline parity. Does not render or establish playable transitions.')
(out/'transition-context-report.json').write_text(json.dumps(report,indent=2))
