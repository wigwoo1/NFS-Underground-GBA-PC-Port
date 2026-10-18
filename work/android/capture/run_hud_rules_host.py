"""Original C oracle for final HUD blending and both window-control domains."""
from pathlib import Path
import argparse,ctypes as C,hashlib,json,os,random,struct,subprocess
p=argparse.ArgumentParser()
for n in ('output','jdk','gcc'):p.add_argument('--'+n,type=Path,required=True)
a=p.parse_args();root=Path(__file__).resolve().parents[1];a.output.mkdir(parents=True,exist_ok=True);hashes={}
for name in ('obj_tile.c','obj_tile.h'):
 data=(root.parent/'camera'/name).read_bytes();(a.output/name).write_bytes(data);hashes[name]=hashlib.sha256(data).hexdigest()
wrapper='''#include "obj_tile.c"
__declspec(dllexport) int window_row_reference(unsigned display,unsigned row,const uint16_t regs[6],uint8_t*out,uint8_t*backdrop){if(!regs||!out||!backdrop||row>=160||(display&0x8000))return 0;uint8_t visible[240],bd[240];for(unsigned x=0;x<240;x++){unsigned control=63;if(display&0x6000){control=regs[5]&63;for(int w=1;w>=0;w--)if((display&(0x2000u<<w))&&obj_window_axis(regs[w],x,240)&&obj_window_axis(regs[w+2],row,160))control=(regs[4]>>(w*8))&63;}visible[x]=control;}obj_backdrop_control_row(display,regs,row,bd);memcpy(out,visible,240);memcpy(backdrop,bd,240);return 1;}
''';(a.output/'hud_reference.c').write_text(wrapper);env=os.environ.copy();env['PATH']=str(a.gcc.parent)+os.pathsep+env['PATH']
def run(command):
 r=subprocess.run(list(map(str,command)),capture_output=True,text=True,env=env)
 if r.returncode:print(r.stdout+r.stderr);r.check_returncode()
 return r.stdout
libpath=a.output/'hud-rules-reference.dll';run([a.gcc,'-O2','-shared',a.output/'hud_reference.c','-o',libpath]);os.add_dll_directory(str(a.gcc.parent));lib=C.CDLL(str(libpath));blend=lib.nf_obj_bg_backdrop_pixel;blend.argtypes=[C.c_uint32]*8;blend.restype=C.c_uint32;windows=lib.window_row_reference;windows.argtypes=[C.c_uint,C.c_uint,C.POINTER(C.c_uint16),C.c_void_p,C.c_void_p];windows.restype=C.c_int
rng=random.Random(912730);pixels=[];window_cases=[]
for effect in range(4):
 for mode in range(2):
  for flags in (0,0x10000,0x20000,0x30000):
   for presence in range(4):
    for alpha in (0,0x0808,0x1010,0x1f1f):
     for target in (0,4,16,32,20,36,48,52):
      for second in (0,0x400,0x1000,0x2000,0x3400):
       pixels.append((0xffc11703 if presence&1 else 0,flags|mode<<2|2,0xff03b7ed if presence&2 else 0,1,0xff031507,effect<<6|target|second,alpha,31 if target&4 else 7))
for i in range(30000):pixels.append((rng.randrange(1<<24)|0xff000000 if i%4 else 0,rng.randrange(4)|rng.randrange(2)<<2|rng.randrange(128)<<8|rng.randrange(4)<<16,rng.randrange(1<<24)|0xff000000 if i%5 else 0,rng.randrange(4),rng.randrange(1<<24)|0xff000000,rng.randrange(16384),rng.randrange(65536),rng.randrange(32)))
# Random wrapped/empty/clamped rectangles and exact zero-length span alignment cases.
for i in range(1000):window_cases.append((rng.choice([0,0x2000,0x4000,0x6000,0x8000]),rng.randrange(160),[rng.randrange(65536) for _ in range(6)]))
for start in (0,1,2,3,4,79,80,159,239,240,241,255):
 for end in (0,1,2,3,4,80,159,239,240,241,255):
  for row in (0,79,159):window_cases.append((0x6000,row,[start<<8|end,0x0101,0x00a0,0xa000,0x3f10,0x20]))
window_cases.extend([(0x2000,160,[0]*6),(0x2000,-1,[0]*6)])
payload=bytearray(struct.pack('>3I',0x31524448,len(pixels),len(window_cases)))
for values in pixels:payload+=struct.pack('>9I',*values,blend(*values))
accepted=rejected=divergent=0
for display,row,regs in window_cases:
 visible=(C.c_uint8*240)(*([165]*240));backdrop=(C.c_uint8*240)(*([90]*240));vb=bytes(visible);bb=bytes(backdrop);good=windows(display,row&0xffffffff,(C.c_uint16*6)(*regs),visible,backdrop)
 if good:accepted+=1;divergent+=sum(x!=y for x,y in zip(visible,backdrop))
 else:rejected+=1;assert bytes(visible)==vb and bytes(backdrop)==bb,'Nonatomic C rejection'
 payload+=struct.pack('>8i',display,row,*regs)+struct.pack('>I',bool(good))
 if good:payload+=bytes(visible)+bytes(backdrop)
assert divergent>0,'No backdrop alignment differences exercised';fixture=a.output/'hud-rules-cases.bin';fixture.write_bytes(payload);classes=a.output/'classes';classes.mkdir(exist_ok=True);files=[root/'java/org/codex/nfsugpreview'/(n+'.java') for n in ('NativeObjScanline','NativeHudRules')]+[root/'tests/org/codex/nfsugpreview/HudRulesTest.java'];run([a.jdk/'bin/javac.exe','--release','8','-d',classes,*files]);stdout=run([a.jdk/'bin/java.exe','-cp',classes,'org.codex.nfsugpreview.HudRulesTest',fixture]);print(stdout,flush=True)
for name,digest in hashes.items():assert hashlib.sha256((root.parent/'camera'/name).read_bytes()).hexdigest()==digest
report={'result':'PASS_HUD_RULES_C_PARITY','blend_cases':len(pixels),'window_cases':len(window_cases),'window_accepted':accepted,'window_rejected':rejected,'exact_window_checks':accepted*480,'visible_backdrop_differences':divergent,'java_stdout':stdout.strip(),'reference_sha256':hashes,'source_sha256':{str(f.relative_to(root)):hashlib.sha256(f.read_bytes()).hexdigest() for f in files},'fixture_sha256':hashlib.sha256(payload).hexdigest(),'scope':'Final blend evaluator and visible/backdrop window controls only; prepared candidate integration and GPU composition remain separate'};(a.output/'hud-rules-host-report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
