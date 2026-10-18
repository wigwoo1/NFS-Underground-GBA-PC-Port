"""Independent original-renderer reference images at exact recorded input indices."""
import ctypes as C,csv,hashlib,json,os,struct,sys,uuid,zlib
from pathlib import Path
p=Path(__file__).resolve().parent;source=Path(sys.argv[1]);rows=list(csv.DictReader(Path(str(source)+'-input.csv').open()));assert rows
prefix=p/'prototype-runs'/('original-video-reference-'+uuid.uuid4().hex)
rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba');state=p.parent/'race.state';dll=p.parent/'nfsprobe.dll'
protected={str(x):hashlib.sha256(x.read_bytes()).hexdigest() for x in (rom,state,dll)}
crt=C.CDLL('msvcrt');crt._putenv.argtypes=[C.c_char_p]
for key in list(os.environ):
 if key.startswith('NF_'):os.environ.pop(key,None);assert crt._putenv((key+'=').encode())==0
indices={int(v) for v in sys.argv[2].split(",")} if len(sys.argv)>2 else {180,250,350,500,600,719};assert indices and min(indices)>=0 and max(indices)<len(rows)
d=C.CDLL(str(dll));d.nf_init.argtypes=[C.c_char_p,C.c_char_p];d.nf_state.argtypes=[C.c_char_p,C.c_int];d.nf_frame.argtypes=[C.c_uint];d.nf_pixels.restype=C.c_void_p;d.nf_dump.argtypes=[C.c_char_p,C.c_uint,C.c_uint];d.nf_read.argtypes=[C.c_uint,C.c_int];d.nf_read.restype=C.c_uint
def chunk(t,b):return struct.pack('>I',len(b))+t+b+struct.pack('>I',zlib.crc32(t+b)&0xffffffff)
def png(raw):
 rgb=b''.join(raw[i:i+3] for i in range(0,len(raw),4));scan=b''.join(b'\0'+rgb[y*720:(y+1)*720] for y in range(160))
 return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>2I5B',240,160,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(scan))+chunk(b'IEND',b'')
images={};evidence=[]
for replay in range(2):
 assert d.nf_init(str(rom).encode(),b'') and d.nf_state(str(state).encode(),0)
 try:
  for row in rows:
   index=int(row['index']);d.nf_frame(int(row['keys']))
   if index in indices:
    pointer=d.nf_pixels();assert pointer;raw=C.string_at(pointer,240*160*4)
    if replay:assert raw==images[index],('original_video_repeat_mismatch',index)
    else:
     images[index]=raw;file=Path(str(prefix)+f'-index-{index:04d}');Path(str(file)+'.rgba').write_bytes(raw);Path(str(file)+'.png').write_bytes(png(raw))
     evidence.append({'index':index,'keys':int(row['keys']),'recorded_refresh':int(row['after']),'post_display_register':d.nf_read(0x04000000,2),'rgba_bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'png':str(file)+'.png'})
  for name,address,size in [('ewram',0x02000000,0x40000),('iwram',0x03000000,0x8000)]:
   file=Path(str(prefix)+f'-replay-{replay}-{name}.bin');d.nf_dump(str(file).encode(),address,size)
   assert file.read_bytes()==Path(str(source)+f'-{name}.bin').read_bytes(),('original_ram_mismatch',name,replay)
 finally:d.nf_close()
assert all(hashlib.sha256(Path(x).read_bytes()).hexdigest()==h for x,h in protected.items())
assert len({r['sha256'] for r in evidence})>1
out={'result':'INDEPENDENT_ORIGINAL_VIDEO_REFERENCES_REPEAT_EXACT','prefix':str(prefix),'input_source':str(source),'original_updates':len(rows),'replays':2,'original_ram_exact':True,'protected_hashes':protected,'images':evidence,'scope':'Complete original 240x160 rendered frames, identical input ledger and final RAM; six integer input indices, no native pixel comparison or fractional-target correspondence established. PNG RGB follows existing host RGBA upload and discards unused alpha; raw RGBA bytes retained.'}
Path(str(prefix)+'-report.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))

