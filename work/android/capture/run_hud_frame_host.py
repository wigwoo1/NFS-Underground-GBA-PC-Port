from pathlib import Path
import argparse,ctypes as C,hashlib,json,os,shutil,struct,subprocess
p=argparse.ArgumentParser()
for n in ('output','bundles','jdk','gcc'):p.add_argument('--'+n,type=Path,required=True)
p.add_argument('--synthetic',type=Path)
a=p.parse_args();root=Path(__file__).resolve().parents[1];a.output.mkdir(parents=True,exist_ok=True);hashes={}
for name in ('obj_tile.c','obj_tile.h'):
 data=(root.parent/'camera'/name).read_bytes();(a.output/name).write_bytes(data);hashes[name]=hashlib.sha256(data).hexdigest()
wrapper='''#include "obj_tile.c"
__declspec(dllexport) int hud_frame_row_reference(const uint8_t*row,uint32_t*out,uint32_t*metadata,uint32_t*parameters){if(!row||!out||!metadata||!parameters)return 0;const uint8_t*r=row+8,*v=row+128,*p=v+98304,*o=p+1024;unsigned display=obj_half(r),blend=obj_half(r+0x50),alpha=obj_half(r+0x52),brightness=obj_half(r+0x54),y;memcpy(&y,row+4,4);if((display&0x8080)||(display&7)!=4)return 0;uint16_t window[6];for(unsigned i=0;i<6;i++)window[i]=obj_half(r+64+i*2);uint32_t colors[240],tags[240],meta[240],params[5];uint8_t visible[240],backdrop[240];if(!nf_obj_window_scanline_prepared(v,98304,p,1024,o,1024,display,y,window,blend,brightness,colors,tags,visible,backdrop))return 0;for(unsigned x=0;x<240;x++){unsigned control=visible[x];if(!(display&0x400))control&=~4u;unsigned flags=128|control|((backdrop[x]&32)?64:0);meta[x]=0xff000000u|(flags<<16)|(tags[x]&3)|(((tags[x]>>2)&3)<<8);}params[0]=obj_color(obj_half(p));params[1]=obj_half(r+12)&3;params[2]=blend;params[3]=alpha;params[4]=brightness;memcpy(out,colors,sizeof(colors));memcpy(metadata,meta,sizeof(meta));memcpy(parameters,params,sizeof(params));return 1;}
''';(a.output/'hud_frame_reference.c').write_text(wrapper);env=os.environ.copy();env['PATH']=str(a.gcc.parent)+os.pathsep+env['PATH']
def run(cmd):
 r=subprocess.run(list(map(str,cmd)),capture_output=True,text=True,env=env)
 if r.returncode:print(r.stdout+r.stderr);r.check_returncode()
 return r.stdout
libpath=a.output/'hud-frame-reference.dll';run([a.gcc,'-O2','-shared',a.output/'hud_frame_reference.c','-o',libpath]);os.add_dll_directory(str(a.gcc.parent));lib=C.CDLL(str(libpath));fn=lib.hud_frame_row_reference;fn.argtypes=[C.c_void_p,C.c_void_p,C.c_void_p,C.c_void_p];fn.restype=C.c_int;fixtures={};nonempty=0
inputs=[(name,a.bundles/(name+'.nab')) for name in ('whole','split')]
if a.synthetic:inputs.append(('synthetic',a.synthetic))
for name,path in inputs:
 raw=path.read_bytes();(a.output/(name+'.nab')).write_bytes(raw);off,size=struct.unpack_from('<QQ',raw,96);layer=raw[off:off+size];colors=bytearray();metadata=bytearray();params=bytearray()
 for y in range(160):
  row=bytearray(layer[32+y*128:32+(y+1)*128])
  for part in range(25):ref=struct.unpack_from('<H',layer,20512+(y*25+part)*2)[0];row+=layer[28512+ref*4096:28512+ref*4096+(2048 if part==24 else 4096)]
  assert len(row)==100480;out=(C.c_uint32*240)();meta=(C.c_uint32*240)();p0=(C.c_uint32*5)();assert fn(bytes(row),out,meta,p0),(name,y);colors+=bytes(out);metadata+=bytes(meta);params+=bytes(p0);nonempty+=sum(x!=0 for x in out)
 golden=colors+metadata+params;(a.output/(name+'.hud')).write_bytes(golden);fixtures[name]={'snapshot_sha256':hashlib.sha256(raw).hexdigest(),'expected_sha256':hashlib.sha256(golden).hexdigest()}
classes=a.output/'classes';classes.mkdir(exist_ok=True);files=[root/'java/org/codex/nfsugpreview'/(n+'.java') for n in ('NativeScenePacket','NativeSceneSnapshot','NativeObjScanline','NativeHudRules','NativeHudCandidates','NativeHudFrame')]+[root/'tests/org/codex/nfsugpreview/HudFrameTest.java'];run([a.jdk/'bin/javac.exe','--release','8','-d',classes,*files]);stdout=run([a.jdk/'bin/java.exe','-cp',classes,'org.codex.nfsugpreview.HudFrameTest',a.output]);print(stdout,flush=True)
for name,digest in hashes.items():assert hashlib.sha256((root.parent/'camera'/name).read_bytes()).hexdigest()==digest
report={'result':'PASS_HISTORICAL_HUD_FRAME_C_PARITY','frames':len(fixtures),'historical_rows':160*len(fixtures),'nontransparent_candidate_pixels':nonempty,'exact_rgba_plane_bytes':307200*len(fixtures),'row_parameter_words':800*len(fixtures),'java_stdout':stdout.strip(),'reference_sha256':hashes,'source_sha256':{str(f.relative_to(root)):hashlib.sha256(f.read_bytes()).hexdigest() for f in files},'fixtures':fixtures,'scope':'Historical HUD color/metadata textures and row parameters only; GPU native-background composition and live integration remain pending'};(a.output/'hud-frame-host-report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
