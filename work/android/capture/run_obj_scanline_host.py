"""Canonical C differential tests for original prepared OBJ candidate scanlines."""
from pathlib import Path
import argparse,ctypes as C,hashlib,json,os,random,struct,subprocess
p=argparse.ArgumentParser()
for n in ('output','snapshot','jdk','gcc'):p.add_argument('--'+n,type=Path,required=True)
a=p.parse_args();root=Path(__file__).resolve().parents[1];a.output.mkdir(parents=True,exist_ok=True);hashes={}
for name in ('obj_tile.c','obj_tile.h'):
 data=(root.parent/'camera'/name).read_bytes();(a.output/name).write_bytes(data);hashes[name]=hashlib.sha256(data).hexdigest()
env=os.environ.copy();env['PATH']=str(a.gcc.parent)+os.pathsep+env['PATH']
def run(cmd):
 r=subprocess.run(list(map(str,cmd)),capture_output=True,text=True,env=env)
 if r.returncode:print(r.stdout+r.stderr);r.check_returncode()
 return r.stdout
libpath=a.output/'obj-scanline-reference.dll';run([a.gcc,'-O2','-shared',a.output/'obj_tile.c','-o',libpath]);os.add_dll_directory(str(a.gcc.parent));lib=C.CDLL(str(libpath));fn=lib.nf_obj_scanline_prepared;fn.argtypes=[C.c_void_p,C.c_size_t,C.c_void_p,C.c_size_t,C.c_void_p,C.c_size_t,C.c_uint16,C.c_uint,C.c_uint,C.c_uint,C.POINTER(C.c_uint32),C.POINTER(C.c_uint32)];fn.restype=C.c_int
rng=random.Random(812721);vram=bytearray(rng.randrange(256) if i%5 else 0 for i in range(98304));palette=bytes(rng.randrange(256) for _ in range(1024));vram[0x14000:0x14020]=bytes([0x11])*32;vram[0x14020:0x14040]=bytes(32);vram[0x14040:0x14060]=bytes([0x22])*32;banks=[(bytes(vram),palette)];cases=[]
def empty():
 oam=bytearray(1024)
 for i in range(128):struct.pack_into('<H',oam,i*8,512)
 return oam
def add(bank,display,row,blend,brightness,oam):cases.append((bank,display,row,blend,brightness,bytes(oam)))
for i in range(600):
 row=rng.randrange(160);display=rng.choice([0,4,64,68])|(0 if i%17==0 else 0x1000);oam=empty()
 for j in range(24):
  shape=rng.randrange(3);size=rng.randrange(4);affine=rng.randrange(2);y=(row+rng.randrange(-60,10))&255;x=rng.randrange(-64,260)&511;a0=y|shape<<14|rng.randrange(2)<<13|rng.randrange(2)<<10|affine<<8|(rng.randrange(2)<<9 if affine else 0);b=x|size<<14|(rng.randrange(4)<<12 if not affine else 0);c=rng.randrange(512,1024)|rng.randrange(4)<<10|rng.randrange(16)<<12;struct.pack_into('<3H',oam,j*8,a0,b,c)
 for j,value in enumerate(rng.choice([[256,0,0,256],[192,64,-32,300],[0,256,-256,0],[-32768,32767,32767,-32768]])):struct.pack_into('<h',oam,6+j*8,value)
 add(0,display,row,rng.randrange(16384),rng.randrange(32),oam)
for blend in (0,0x90,0xd0,0x2490,0x24d0):
 oam=empty()
 for j,(tile,priority) in enumerate(((512,3),(513,0),(514,1))):struct.pack_into('<3H',oam,j*8,50,10,tile|priority<<10)
 add(0,0x1044,50,blend,9,oam)
for mode in (0x800,0xc00,0x1000):
 oam=empty();struct.pack_into('<3H',oam,0,mode,0,512);add(0,0x1004,0,0,0,oam)
for display,row in ((0x3004,0),(0x9004,0),(0x1004,160),(0x1004,-1)) :add(0,display,row,0,0,empty())
bundle=a.snapshot.read_bytes();off,size=struct.unpack_from('<QQ',bundle,96);layer=bundle[off:off+size]
for row in (0,79,159):
 pieces=[]
 for part in range(25):ref=struct.unpack_from('<H',layer,20512+(row*25+part)*2)[0];pieces.append(layer[28512+ref*4096:28512+ref*4096+(2048 if part==24 else 4096)])
 banks.append((b''.join(pieces[:24]),pieces[24][:1024]));oam=pieces[24][1024:];registers=layer[32+row*128+8:32+row*128+104];display=struct.unpack_from('<H',registers)[0]&~0xe000;blend=struct.unpack_from('<H',registers,0x50)[0];bright=struct.unpack_from('<H',registers,0x54)[0]
 for be,br in ((blend,bright),(0,0),(0x90,8),(0xd0,16),(0x2490,31)):add(len(banks)-1,display,row,be,br,oam)
payload=bytearray(struct.pack('>3I',0x31534a4f,len(banks),len(cases)))
for v,pal in banks:payload+=v+pal
accepted=rejected=0
for bank,display,row,blend,brightness,oam in cases:
 v,pal=banks[bank];colors=(C.c_uint32*240)(*([0xa5a5a5a5]*240));tags=(C.c_uint32*240)(*([0x5a5a5a5a]*240));cb=bytes(colors);tb=bytes(tags);good=fn(v,len(v),pal,len(pal),oam,len(oam),display,row&0xffffffff,blend,brightness,colors,tags)
 if good:accepted+=1
 else:rejected+=1;assert bytes(colors)==cb and bytes(tags)==tb,'Nonatomic C rejection'
 payload+=struct.pack('>5i',bank,display,row,blend,brightness)+oam+struct.pack('>I',bool(good))
 if good:payload+=struct.pack('>240I',*colors)+struct.pack('>240I',*tags)
fixture=a.output/'obj-scanline-cases.bin';fixture.write_bytes(payload);files=[root/'java/org/codex/nfsugpreview/NativeObjScanline.java',root/'tests/org/codex/nfsugpreview/ObjScanlineTest.java'];classes=a.output/'classes';classes.mkdir(exist_ok=True);run([a.jdk/'bin/javac.exe','--release','8','-d',classes,*files]);stdout=run([a.jdk/'bin/java.exe','-cp',classes,'org.codex.nfsugpreview.ObjScanlineTest',fixture]);print(stdout,flush=True)
for name,digest in hashes.items():assert hashlib.sha256((root.parent/'camera'/name).read_bytes()).hexdigest()==digest
report={'result':'PASS_PREPARED_OBJ_SCANLINE_C_PARITY','cases':len(cases),'accepted':accepted,'rejected':rejected,'exact_color_and_tag_checks':accepted*480,'retained_rows':[0,79,159],'synthetic_random_cases':600,'transparent_priority_cases':5,'retained_game_cases':15,'java_stdout':stdout.strip(),'reference_sha256':hashes,'source_sha256':{str(f.relative_to(root)):hashlib.sha256(f.read_bytes()).hexdigest() for f in files},'fixture_sha256':hashlib.sha256(payload).hexdigest(),'scope':'Prepared OBJ candidates and metadata only; window/backdrop controls, final HUD blending, Android runtime/GPU remain separate'};(a.output/'obj-scanline-host-report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
