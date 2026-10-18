"""Read-only checkpoint scene-boundary inventory, original logic parity."""
import ctypes as C,hashlib,json,struct,sys
from pathlib import Path
from PIL import Image,ImageDraw
updates=int(sys.argv[1]) if len(sys.argv)>1 else 40;selected=sys.argv[2] if len(sys.argv)>2 else None
p=Path(__file__).resolve().parent;outdir=p/('prototype-runs/lifecycle-inventory' if not selected else f'prototype-runs/lifecycle-{selected}-{updates}');outdir.mkdir(exist_ok=True);rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba');raw=rom.read_bytes();P=C.c_void_p;Sink=C.CFUNCTYPE(C.c_int,P,C.c_uint64,P,C.c_size_t)
bridge=C.CDLL(str(p/'visibility-probe-wide.dll'));baseline=C.CDLL(str(p.parent/'nfsprobe.dll'))
for dll in [bridge,baseline]:
 dll.nf_init.argtypes=[C.c_char_p]*2;dll.nf_state.argtypes=[C.c_char_p,C.c_int];dll.nf_dump.argtypes=[C.c_char_p,C.c_uint,C.c_uint];dll.nf_pixels.restype=P;dll.nf_read.argtypes=[C.c_uint,C.c_int]
bridge.nf_native_scene_sink.argtypes=[Sink,P];bridge.nf_live_visibility_enable.argtypes=[P,C.c_size_t,C.c_size_t];results=[]
paths=sorted((p.parent/'fix-menu').glob('stage-*.state'))+sorted((p.parent/'fix-menu').glob('menu-*.state'))
if selected:paths=[state for state in paths if state.stem==selected];assert paths
for state in paths:
 state_hash=hashlib.sha256(state.read_bytes()).hexdigest();packets=[]
 @Sink
 def sink(ctx,epoch,data,size):
  packet=C.string_at(data,size);sections={t:packet[o:o+n] for t,o,n in (struct.unpack_from('<3I',packet,32+j*12) for j in range(5))};model=sections[1];packets.append(dict(epoch=epoch,bytes=size,models=struct.unpack_from('<I',model,4)[0] if model[:4]==b'NML1' else 1,world=struct.unpack_from('<I',sections[2],4)[0]));return 1
 assert bridge.nf_init(str(rom).encode(),b'') and bridge.nf_state(str(state).encode(),0);assert bridge.nf_native_scene_sink(sink,None) and bridge.nf_native_scene_multimodel(1) and bridge.nf_live_visibility_enable(raw,len(raw),16*1024*1024) and bridge.nf_layer_queue_enable(1);bridge.nf_live_surface_audit_enable(1)
 actual=[]
 try:
  for _ in range(updates):bridge.nf_frame(0)
  rgba=C.string_at(bridge.nf_pixels(),240*160*4);im=Image.frombytes('RGBA',(240,160),rgba).convert('RGB');im.save(outdir/(state.stem+'.png'));display=bridge.nf_read(0x04000000,2)
  for name,base,n in [('ewram',0x02000000,0x40000),('iwram',0x03000000,0x8000)]:
   path=outdir/(state.stem+'-'+name+'.bin');bridge.nf_dump(str(path).encode(),base,n);actual.append(path.read_bytes())
 finally:bridge.nf_close()
 assert baseline.nf_init(str(rom).encode(),b'') and baseline.nf_state(str(state).encode(),0)
 try:
  for _ in range(updates):baseline.nf_frame(0)
  for expected,(name,base,n) in zip(actual,[('ewram',0x02000000,0x40000),('iwram',0x03000000,0x8000)]):
   path=outdir/(state.stem+'-baseline-'+name+'.bin');baseline.nf_dump(str(path).encode(),base,n);assert path.read_bytes()==expected,state
 finally:baseline.nf_close()
 assert hashlib.sha256(state.read_bytes()).hexdigest()==state_hash
 results.append(dict(state=str(state),state_sha256=state_hash,display=display,original_updates=updates,exact_original_ram=True,native_scene_packets=len(packets),model_counts=sorted(set(v['models'] for v in packets)),world_counts=sorted(set(v['world'] for v in packets))));print(state.stem,len(packets),flush=True)
contact=Image.new('RGB',(960,((len(paths)+3)//4)*190));draw=ImageDraw.Draw(contact)
for i,state in enumerate(paths):
 x=(i%4)*240;y=(i//4)*190;contact.paste(Image.open(outdir/(state.stem+'.png')),(x,y));draw.text((x+4,y+162),f"{state.stem}: {results[i]['native_scene_packets']} scene packets",fill='white')
contact.save(outdir/'contact.png');(outdir/'report.json').write_text(json.dumps(dict(result='PASS',rom_sha256=hashlib.sha256(raw).hexdigest(),checks=results,scope='Configured neutral original updates per saved checkpoint, bridge instrumentation completeRAM parity; original240x160 framebuffer thumbnails identify states only. Native packet availability is not menu rendering or playable lifecycle proof. Saved states read-only.'),indent=2))
