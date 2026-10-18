from pathlib import Path
import argparse,ctypes as C,hashlib,json,os,random,struct,subprocess
p=argparse.ArgumentParser()
for n in ('output','candidates','jdk','gcc'):p.add_argument('--'+n,type=Path,required=True)
a=p.parse_args();root=Path(__file__).resolve().parents[1];a.output.mkdir(parents=True,exist_ok=True);hashes={}
for name in ('obj_tile.c','obj_tile.h'):
 data=(root.parent/'camera'/name).read_bytes();(a.output/name).write_bytes(data);hashes[name]=hashlib.sha256(data).hexdigest()
env=os.environ.copy();env['PATH']=str(a.gcc.parent)+os.pathsep+env['PATH']
def run(cmd):
 r=subprocess.run(list(map(str,cmd)),capture_output=True,text=True,env=env)
 if r.returncode:print(r.stdout+r.stderr);r.check_returncode()
 return r.stdout
libpath=a.output/'hud-candidates-reference.dll';run([a.gcc,'-O2','-shared',a.output/'obj_tile.c','-o',libpath]);os.add_dll_directory(str(a.gcc.parent));lib=C.CDLL(str(libpath));fn=lib.nf_obj_window_scanline_prepared;fn.argtypes=[C.c_void_p,C.c_size_t,C.c_void_p,C.c_size_t,C.c_void_p,C.c_size_t,C.c_uint16,C.c_uint,C.POINTER(C.c_uint16),C.c_uint,C.c_uint,C.c_void_p,C.c_void_p,C.c_void_p,C.c_void_p];fn.restype=C.c_int
source=a.candidates.read_bytes();magic,bcount,case_count=struct.unpack_from('>3I',source);assert magic==0x31534a4f;at=12;banks=[]
for i in range(bcount):banks.append((source[at:at+98304],source[at+98304:at+99328]));at+=99328
base=[]
for i in range(case_count):
 bank,display,row,blend,brightness=struct.unpack_from('>5i',source,at);at+=20;oam=source[at:at+1024];at+=1024;good=struct.unpack_from('>I',source,at)[0];at+=4+(1920 if good else 0);base.append((bank,display,row,blend,brightness,oam))
assert at==len(source);rng=random.Random(49127);cases=[]
for bank,display,row,blend,brightness,oam in base:
 for mode in (0,0x2000,0x6000):
  window=[rng.randrange(65536) for _ in range(6)] if mode else [0,0,0,0,0,0];cases.append((bank,(display&~0x6000)|mode,row,blend,brightness,window,oam))
payload=bytearray(struct.pack('>3I',0x3143484e,bcount,len(cases)))
for v,pal in banks:payload+=v+pal
accepted=rejected=0
for bank,display,row,blend,brightness,window,oam in cases:
 v,pal=banks[bank];colors=(C.c_uint32*240)(*([0xa5a5a5a5]*240));tags=(C.c_uint32*240)(*([0x5a5a5a5a]*240));visible=(C.c_uint8*240)(*([123]*240));backdrop=(C.c_uint8*240)(*([231]*240));before=[bytes(b) for b in (colors,tags,visible,backdrop)];good=fn(v,len(v),pal,len(pal),oam,len(oam),display,row&0xffffffff,(C.c_uint16*6)(*window),blend,brightness,colors,tags,visible,backdrop)
 if good:accepted+=1
 else:rejected+=1;assert before==[bytes(b) for b in (colors,tags,visible,backdrop)],'Nonatomic C rejection'
 payload+=struct.pack('>11i',bank,display,row,blend,brightness,*window)+oam+struct.pack('>I',bool(good))
 if good:payload+=struct.pack('>240I',*colors)+struct.pack('>240I',*tags)+bytes(visible)+bytes(backdrop)
fixture=a.output/'hud-candidates-cases.bin';fixture.write_bytes(payload);classes=a.output/'classes';classes.mkdir(exist_ok=True);files=[root/'java/org/codex/nfsugpreview'/(n+'.java') for n in ('NativeObjScanline','NativeHudRules','NativeHudCandidates')]+[root/'tests/org/codex/nfsugpreview/HudCandidatesTest.java'];run([a.jdk/'bin/javac.exe','--release','8','-d',classes,*files]);stdout=run([a.jdk/'bin/java.exe','-cp',classes,'org.codex.nfsugpreview.HudCandidatesTest',fixture]);print(stdout,flush=True)
for name,digest in hashes.items():assert hashlib.sha256((root.parent/'camera'/name).read_bytes()).hexdigest()==digest
report={'result':'PASS_HUD_CANDIDATES_C_PARITY','cases':len(cases),'accepted':accepted,'rejected':rejected,'exact_checks':accepted*960,'java_stdout':stdout.strip(),'reference_sha256':hashes,'source_sha256':{str(f.relative_to(root)):hashlib.sha256(f.read_bytes()).hexdigest() for f in files},'fixture_sha256':hashlib.sha256(payload).hexdigest(),'source_candidate_fixture_sha256':hashlib.sha256(source).hexdigest(),'scope':'Window-filtered OBJ candidates/colors/tags/visible/backdrop controls; native background blending and GPU integration not yet enabled'};(a.output/'hud-candidates-host-report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
