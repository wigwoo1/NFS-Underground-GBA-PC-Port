"""Compare original regular and affine OBJ assets with canonical obj_tile.c."""
from pathlib import Path
import argparse,ctypes as C,hashlib,json,os,random,struct,subprocess
p=argparse.ArgumentParser()
for n in ('output','jdk','gcc'):p.add_argument('--'+n,type=Path,required=True)
p.add_argument('--snapshot',type=Path);p.add_argument('--row',type=int,default=79)
a=p.parse_args();root=Path(__file__).resolve().parents[1];a.output.mkdir(parents=True,exist_ok=True);hashes={}
for name in ('obj_tile.c','obj_tile.h'):
 data=(root.parent/'camera'/name).read_bytes();(a.output/name).write_bytes(data);hashes[name]=hashlib.sha256(data).hexdigest()
env=os.environ.copy();env['PATH']=str(a.gcc.parent)+os.pathsep+env['PATH']
def run(cmd):
 r=subprocess.run(list(map(str,cmd)),capture_output=True,text=True,env=env)
 if r.returncode:print(r.stdout+r.stderr);r.check_returncode()
 return r.stdout
libpath=a.output/'obj-image-reference.dll';run([a.gcc,'-O2','-shared',a.output/'obj_tile.c','-o',libpath]);os.add_dll_directory(str(a.gcc.parent));lib=C.CDLL(str(libpath));regular=lib.nf_obj_image;regular.argtypes=[C.c_void_p,C.c_size_t,C.c_void_p,C.c_size_t,*([C.c_uint16]*4),C.POINTER(C.c_uint32),C.c_size_t,C.POINTER(C.c_uint)];regular.restype=C.c_int;affine=lib.nf_obj_affine_image;affine.argtypes=[C.c_void_p,C.c_size_t,C.c_void_p,C.c_size_t,*([C.c_uint16]*4),C.POINTER(C.c_int16),C.POINTER(C.c_uint32),C.c_size_t,C.POINTER(C.c_uint)];affine.restype=C.c_int
rng=random.Random(88117);vram=bytes(rng.randrange(256) if i%7 else 0 for i in range(0x18000));palette=bytes(rng.randrange(256) for _ in range(1024));oam=None;display_captured=0
if a.snapshot:
 bundle=a.snapshot.read_bytes();off,size=struct.unpack_from('<QQ',bundle,96);layer=bundle[off:off+size];assert 0<=a.row<160;pieces=[]
 for part in range(25):ref=struct.unpack_from('<H',layer,20512+(a.row*25+part)*2)[0];pieces.append(layer[28512+ref*4096:28512+ref*4096+(2048 if part==24 else 4096)])
 vram=b''.join(pieces[:24]);palette=pieces[24][:1024];oam=pieces[24][1024:];display_captured=struct.unpack_from('<H',layer,32+a.row*128+8)[0]
(a.output/'obj-vram.bin').write_bytes(vram);(a.output/'obj-palette.bin').write_bytes(palette);cases=[]
for shape in range(3):
 for size in range(4):
  for color8 in range(2):
   for one in range(2):
    for flip in range(4):
     for bitmap in range(2):
      tile=rng.randrange(512 if bitmap else 0,1024);a0=shape<<14|color8<<13|((tile&1)<<10);b=size<<14|((flip&1)<<12)|((flip>>1)<<13);c=tile|rng.randrange(4)<<10|rng.randrange(16)<<12;display=(4 if bitmap else 0)|(64 if one else 0);cases.append((0,a0,b,c,display,[256,0,0,256]))
matrices=([256,0,0,256],[0,256,-256,0],[192,64,-32,300],[-32768,32767,32767,-32768])
for shape in range(3):
 for size in range(4):
  for color8 in range(2):
   for one in range(2):
    for double in range(2):
     for matrix in matrices:
      tile=rng.randrange(512,1024);cases.append((1,shape<<14|color8<<13|256|double<<9,size<<14|rng.randrange(0x4000),tile|rng.randrange(16)<<12,4|(64 if one else 0),matrix))
for _ in range(128):cases.append((rng.randrange(2),rng.randrange(65536),rng.randrange(65536),rng.randrange(65536),rng.choice([0,4,64,68]),[rng.randint(-32768,32767) for _ in range(4)]))
for kind,a0,b,c,display in [(0,0x200,0,512,4),(0,0x100,0,512,4),(0,0x800,0,512,4),(0,0xc000,0,512,4),(0,0,0,511,4),(1,0,0,512,4),(1,0x100,0,511,4)]:cases.append((kind,a0,b,c,display,[256,0,0,256]))
if oam is not None:
 for i in range(128):
  a0,b,c=struct.unpack_from('<3H',oam,i*8);kind=int(bool(a0&256));matrix=[struct.unpack_from('<h',oam,((b>>9)&31)*32+6+j*8)[0] for j in range(4)];cases.append((kind,a0,b,c,display_captured,matrix))
payload=bytearray(struct.pack('>2I',0x314a424f,len(cases)));accepted=rejected=texels=0
for kind,a0,b,c,display,matrix in cases:
 out=(C.c_uint32*16384)(*([0xa5a5a5a5]*16384));before=bytes(out);dimensions=(C.c_uint*2)(7777,8888)
 if kind==0:good=regular(vram,len(vram),palette,len(palette),a0,b,c,display,out,16384,dimensions)
 else:good=affine(vram,len(vram),palette,len(palette),a0,b,c,display,(C.c_int16*4)(*matrix),out,16384,dimensions)
 w,h=dimensions if good else (0,0)
 if good:accepted+=1;texels+=w*h
 else:rejected+=1;assert bytes(out)==before and list(dimensions)==[7777,8888],'Non-atomic C rejection'
 payload+=struct.pack('>12I',kind,a0,b,c,display,*[x&0xffffffff for x in matrix],bool(good),w,h)+struct.pack('>'+str(w*h)+'I',*list(out)[:w*h])
fixture=a.output/'obj-image-cases.bin';fixture.write_bytes(payload);files=[root/'java/org/codex/nfsugpreview/NativeObjImage.java',root/'tests/org/codex/nfsugpreview/ObjImageTest.java'];classes=a.output/'classes';classes.mkdir(exist_ok=True);run([a.jdk/'bin/javac.exe','--release','8','-d',classes,*files]);stdout=run([a.jdk/'bin/java.exe','-cp',classes,'org.codex.nfsugpreview.ObjImageTest',a.output/'obj-vram.bin',a.output/'obj-palette.bin',fixture]);print(stdout,flush=True)
for name,digest in hashes.items():assert hashlib.sha256((root.parent/'camera'/name).read_bytes()).hexdigest()==digest
report={'result':'PASS_OBJ_IMAGE_C_PARITY','cases':len(cases),'accepted':accepted,'rejected':rejected,'exact_rgba_texels':texels,'regular_cases':sum(c[0]==0 for c in cases),'affine_cases':sum(c[0]==1 for c in cases),'java_stdout':stdout.strip(),'reference_sha256':hashes,'source_sha256':{str(f.relative_to(root)):hashlib.sha256(f.read_bytes()).hexdigest() for f in files},'fixture_sha256':hashlib.sha256(payload).hexdigest(),'vram_sha256':hashlib.sha256(vram).hexdigest(),'palette_sha256':hashlib.sha256(palette).hexdigest(),'retained_snapshot':str(a.snapshot) if a.snapshot else None,'retained_row':a.row if a.snapshot else None,'captured_oam_cases':128 if oam is not None else 0,'scope':'Sprite asset decoding only: synthetic cases plus optional retained game VRAM/palette/OAM; no HUD priority/window/effect composition, Android runtime or GPU proof'};(a.output/'obj-image-host-report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
