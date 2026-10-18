"""Original source records for exact retained stable interval, preserved inputs."""
from pathlib import Path
import ctypes as C,csv,json,hashlib,os
from scene_batches import batches
p=Path('work/camera').resolve();source=p/'prototype-runs/racing-motion-audit-a88232ac136d4ad58dc7231b706de812';rows=list(csv.DictReader(Path(str(source)+'-input.csv').open()));rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba');state=p.parent/'race.state';dll=p/'visibility-probe-wide.dll';protected={str(x):hashlib.sha256(x.read_bytes()).hexdigest() for x in (rom,state,p.parent/'nfsprobe.dll')}
crt=C.CDLL('msvcrt');crt._putenv.argtypes=[C.c_char_p]
for k in list(os.environ):
 if k.startswith('NF_'):os.environ.pop(k,None);assert crt._putenv((k+'=').encode())==0
os.environ['NF_TRACE_ROAD_EDGE_ANIMATIONS']='1';assert crt._putenv(b'NF_TRACE_ROAD_EDGE_ANIMATIONS=1')==0
trace=p/'motion-original-source-8750-8781.bin';d=C.CDLL(str(dll));d.nf_init.argtypes=[C.c_char_p]*2;d.nf_state.argtypes=[C.c_char_p,C.c_int];d.nf_world_trace.argtypes=[C.c_char_p];d.nf_dump.argtypes=[C.c_char_p,C.c_uint,C.c_uint];d.nf_native_scene_refresh.restype=C.c_uint
assert d.nf_init(str(rom).encode(),b'') and d.nf_state(str(state).encode(),0);started=False;ended=False
try:
 for row in rows:
  before=d.nf_native_scene_refresh()
  if before>=8749 and not started:assert d.nf_world_trace(str(trace).encode());started=True
  d.nf_frame(int(row['keys']))
  if started and not ended and d.nf_native_scene_refresh()>=8781:d.nf_world_trace(None);ended=True
 assert started and ended
 for name,base,size in [('ewram',0x02000000,0x40000),('iwram',0x03000000,0x8000)]:
  target=p/f'motion-original-source-{name}.bin';d.nf_dump(str(target).encode(),base,size);assert target.read_bytes()==Path(str(source)+'-'+name+'.bin').read_bytes(),name
finally:d.nf_world_trace(None);d.nf_close()
selected=[b for b in batches(trace) if b['begin_refresh']>=8750 and b['end_refresh']<=8781];assert len(selected)>=2
scenes=[]
for batch in selected:
 roads=[e for e in batch['events'] if e['pc']==0x030032f0]
 scenes.append(dict(begin=batch['begin_refresh'],end=batch['end_refresh'],page=batch['display_page'],roads=[dict(event=e['id'],refresh=e['frame'],source=e['blocks'][4][0],blocks={str(k):dict(address=a,hex=data.hex()) for k,(a,data) in e['blocks'].items()}) for e in roads]))
report=dict(result='ORIGINAL_MOTION_INTERVALS_CAPTURED',scenes=scenes,trace_sha256=hashlib.sha256(trace.read_bytes()).hexdigest(),original_final_ram_exact=True,scope='Read-only original road source records and matrix blocks across consecutive completed game scenes replayed from unchanged race state/input ledger. Current interpolated world pose not inferred from screen polygons; raw prepared streams are oracle only.')
assert all(hashlib.sha256(Path(x).read_bytes()).hexdigest()==v for x,v in protected.items());(p/'motion-original-road-source-intervals.json').write_text(json.dumps(report,indent=2));print(dict(result=report['result'],scenes=len(scenes),roads=sum(len(s['roads']) for s in scenes),trace_bytes=trace.stat().st_size,original_final_ram_exact=True))
