"""Bounded original draw entry/return VRAM evidence, with stable RAM replay."""
import ctypes as C,json,hashlib,struct,uuid,argparse
from pathlib import Path
import numpy as np
from scene_batches import records
args=argparse.ArgumentParser();args.add_argument('--warmup',type=int,default=900);args.add_argument('--updates',type=int,default=30);config=args.parse_args()
assert 0<=config.warmup<=20000 and 1<=config.updates<=200
p=Path(__file__).resolve().parent;prefix=p/'prototype-runs'/('original-draw-vram-'+uuid.uuid4().hex)
rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba');state=p.parent/'driving.state'
hashes=[hashlib.sha256(f.read_bytes()).hexdigest() for f in (rom,state)]
crt=C.CDLL('msvcrt');crt._putenv.argtypes=[C.c_char_p];assert crt._putenv(b'NF_TRACE_DRAW_FRAMEBUFFER=1')==0
d=C.CDLL(str(p/'visibility-probe-wide.dll'));d.nf_init.argtypes=[C.c_char_p]*2;d.nf_state.argtypes=[C.c_char_p,C.c_int];d.nf_world_trace.argtypes=[C.c_char_p];d.nf_dump.argtypes=[C.c_char_p,C.c_uint,C.c_uint]
ledger=[1|(32 if 180<=i<500 else 16 if 500<=i<720 else 0) for i in range(config.warmup+config.updates)]
trace=Path(str(prefix)+'.bin');assert d.nf_init(str(rom).encode(),b'') and d.nf_state(str(state).encode(),0)
try:
 for i,keys in enumerate(ledger):
  if i==config.warmup:assert d.nf_world_trace(str(trace).encode())
  d.nf_frame(keys)
 d.nf_world_trace(None)
 for name,base,size in [('ewram',0x02000000,0x40000),('iwram',0x03000000,0x8000)]:d.nf_dump((str(prefix)+'-'+name+'.bin').encode(),base,size)
finally:d.nf_close()
baseline=C.CDLL(str(p.parent/'nfsprobe.dll'));baseline.nf_init.argtypes=[C.c_char_p]*2;baseline.nf_state.argtypes=[C.c_char_p,C.c_int];baseline.nf_dump.argtypes=[C.c_char_p,C.c_uint,C.c_uint]
assert baseline.nf_init(str(rom).encode(),b'') and baseline.nf_state(str(state).encode(),0)
try:
 for keys in ledger:baseline.nf_frame(keys)
 for name,base,size in [('ewram',0x02000000,0x40000),('iwram',0x03000000,0x8000)]:
  file=Path(str(prefix)+'-replay-'+name+'.bin');baseline.nf_dump(str(file).encode(),base,size)
  expected=file.read_bytes();actual=Path(str(prefix)+'-'+name+'.bin').read_bytes()
  assert len(actual)==len(expected)==size and actual==expected,name
finally:baseline.nf_close()
pending={};checks=[];flips=0
for e in records(trace):
 if e['pc']==0x04000000:flips+=1
 if e['pc']!=0xffff0084:continue
 assert e['blocks'][84][0]==0x06000000 and len(e['blocks'][84][1])==0x18000
 metadata=e['blocks'][85][1];stage,identity,pc,lr,sp,stateaddr,source,dispcnt=struct.unpack('<8I',metadata[:32]);image=e['blocks'][84][1]
 if stage==0:
  assert identity not in pending;pending[identity]=(pc,lr,sp,stateaddr,source,e['frame'],image,dispcnt)
 elif stage==1:
  assert stage==1 and identity in pending
  start=pending.pop(identity);assert start[:5]==(pc,lr,sp,stateaddr,source)
  changed=np.frombuffer(start[6],np.uint8)!=np.frombuffer(image,np.uint8)
  checks.append(dict(id=identity,pc=hex(pc),source=hex(source),start_refresh=start[5],end_refresh=e['frame'],dispcnt_before=start[7],dispcnt_after=dispcnt,changed_vram_bytes=int(changed.sum()),before_sha256=hashlib.sha256(start[6]).hexdigest(),after_sha256=hashlib.sha256(image).hexdigest()))
  if len(metadata)==44:
   writes,write_bytes,polygon_calls=struct.unpack_from('<3I',metadata,32);checks[-1].update(vram_store_calls=writes,vram_store_bytes=write_bytes,original_polygon_calls=polygon_calls)
 else:assert stage==2 and identity in pending
assert checks and any(c['changed_vram_bytes'] for c in checks)
assert hashes==[hashlib.sha256(f.read_bytes()).hexdigest() for f in (rom,state)]
report=dict(result='CAPTURED',original_updates=len(ledger),warmup=config.warmup,traced_updates=config.updates,trace=str(trace),trace_sha256=hashlib.sha256(trace.read_bytes()).hexdigest(),completed_draws=checks,unmatched_entries=list(pending),page_flips=flips,exact_original_ram=True,scope='Original road/wall entry-return snapshots matched by LR/SP/mode; model04770 closes at source epilogue048B0 with entry SP. Flip snapshots are separate boundary records. Value changes omit identical-value writes. No native raster parity or smooth gameplay claim.')
target=Path(str(prefix)+'-verification.json');target.write_text(json.dumps(report,indent=2));print(json.dumps(dict(report=str(target),completed=len(checks),unmatched=len(pending),changed_draws=sum(bool(c['changed_vram_bytes']) for c in checks),kinds=sorted(set(c['pc'] for c in checks)),exact_original_ram=True)))
