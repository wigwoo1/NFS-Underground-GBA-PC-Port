"""Replay actual logged keys through original core without the native renderer."""
import ctypes as C,json,sys,hashlib,struct,zlib
from pathlib import Path
rp,cp=map(Path,sys.argv[1:3]);cp.mkdir(exist_ok=True);r=json.loads(rp.read_text());rows=r['startup_inputs']+r['inputs'];assert rows and r['original_updates']==len(r['inputs'])
assert all(b['refresh']==a['refresh']+1 for a,b in zip(rows,rows[1:]))
d=C.CDLL(str(Path('work/nfsprobe.dll').resolve()));d.nf_init.argtypes=[C.c_char_p,C.c_char_p];d.nf_state.argtypes=[C.c_char_p,C.c_int];d.nf_dump.argtypes=[C.c_char_p,C.c_uint,C.c_uint]
rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba');state=Path('work/race.state');before={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (rom,state)}
assert d.nf_init(str(rom).encode(),b'') and d.nf_state(str(state.resolve()).encode(),0)
checks=[];video=[]
indices=set(map(int,sys.argv[3].split(','))) if len(sys.argv)>3 else set()
assert all(0<=i<len(rows) for i in indices)
d.nf_pixels.restype=C.c_void_p;d.nf_native_scene_refresh.restype=C.c_uint
def png(raw):
 def chunk(t,b):return struct.pack('>I',len(b))+t+b+struct.pack('>I',zlib.crc32(t+b)&0xffffffff)
 rgb=b''.join(raw[i:i+3] for i in range(0,len(raw),4));scan=b''.join(b'\0'+rgb[y*720:(y+1)*720] for y in range(160))
 return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>2I5B',240,160,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(scan))+chunk(b'IEND',b'')
try:
 for index,x in enumerate(rows):
  assert int(d.nf_native_scene_refresh())==x['refresh']
  d.nf_frame(x['keys'])
  assert int(d.nf_native_scene_refresh())==x['refresh']+1
  if index in indices:
   address=d.nf_pixels();assert address;raw=C.string_at(address,240*160*4);path=cp/f'original-index-{index:05d}';path.with_suffix('.rgba').write_bytes(raw);path.with_suffix('.png').write_bytes(png(raw));video.append(dict(input_index=index,input_before_refresh=x['refresh'],refresh=int(d.nf_native_scene_refresh()),keys=x['keys'],rgba_sha256=hashlib.sha256(raw).hexdigest(),png=str(path.with_suffix('.png')),scope='Original core pixels after this input; native target matching and fractional fidelity not established'))
 for name,address,size in [('ewram',0x02000000,0x40000),('iwram',0x03000000,0x8000)]:
  out=cp/('baseline-'+name+'.bin');d.nf_dump(str(out.resolve()).encode(),address,size);data=out.read_bytes();expected=Path(r['final_ram'][name]['path']).read_bytes();assert len(data)==len(expected)==size
  diff=[i for i,(a,b) in enumerate(zip(data,expected)) if a!=b]
  checks.append(dict(region=name,bytes=size,exact=data==expected,baseline_sha256=hashlib.sha256(data).hexdigest(),live_sha256=hashlib.sha256(expected).hexdigest(),different_bytes=len(diff),first_differences=diff[:16]))
finally:d.nf_close()
assert before=={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (rom,state)}
result=dict(original_video_references=video,result='PASS' if all(x['exact'] for x in checks) else 'MISMATCH',report=str(rp),original_frames=len(rows),regions=checks,protected_rom_state_unchanged=True,scope='Exact final EWRAM/IWRAM after recorded startup/game inputs replayed in renderer-free original core; does not certify rendering fidelity, scanout or physical controller')
(cp/'game-state-replay.json').write_text(json.dumps(result,indent=2));print(json.dumps(result));assert result['result']=='PASS'
