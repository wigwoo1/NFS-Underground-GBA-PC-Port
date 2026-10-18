from pathlib import Path
import ctypes as C,csv,json,hashlib
p=Path('work/camera').resolve();rows=[{k:int(v) for k,v in r.items()} for r in csv.DictReader(open(p/'refresh-timing.csv'))];assert len(rows)==3583
for i,r in enumerate(rows):
 assert r['index']==i and r['after']==r['before']+1 and r['keys']==(1|(32 if 180<=i<500 else 16 if 500<=i<720 else 0))
d=C.CDLL(str(p.parent/'nfsprobe.dll'));d.nf_init.argtypes=[C.c_char_p]*2;d.nf_state.argtypes=[C.c_char_p,C.c_int];d.nf_dump.argtypes=[C.c_char_p,C.c_uint,C.c_uint]
assert d.nf_init(b'G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba',b'') and d.nf_state(str(p.parent/'driving.state').encode(),0)
hashes={}
try:
 for r in rows:d.nf_frame(r['keys'])
 for name,address,size in [('ewram',0x02000000,0x40000),('iwram',0x03000000,0x8000)]:
  file=p/f'long-route-baseline-{name}.bin';d.nf_dump(str(file).encode(),address,size);actual=(p/f'live-paired-parity-{name}.bin').read_bytes();assert actual==file.read_bytes(),name;hashes[name]=hashlib.sha256(actual).hexdigest()
finally:d.nf_close()
present=list(csv.DictReader(open(p/'live-paired-parity.csv')));first=next(r for r in present if int(r['ready'])==0 and int(r['display_index'])>20)
r=dict(result='STATE_PARITY_PASS_SCENE_RENDERING_FAIL',refreshes=len(rows),every_refresh_once=True,ram_hashes=hashes,ready=sum(int(r['ready']) for r in present),unavailable=sum(not int(r['ready']) for r in present),first_late_unavailable_display=int(first['display_index']),scope='Failed60sec multi-car native scene run preserves all original refreshes/inputs and final game RAM; rendering failure remains unresolved')
(p/'long-route-state-parity.json').write_text(json.dumps(r,indent=2));print(r)
