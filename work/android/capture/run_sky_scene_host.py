from pathlib import Path
import struct,hashlib,subprocess,json,argparse
p=argparse.ArgumentParser();p.add_argument("--fixtures",type=Path,default=Path(r"C:\NFSUG-Workspace\NFSUG-android-owned-text-local"));a=p.parse_args()
root=Path(__file__).resolve().parents[3];out=a.fixtures;fixtures={}
for name in ('whole','split'):
 raw=(out/f'sky-scene-{name}.nsb').read_bytes();h=struct.unpack_from('<16Q',raw);scene=raw[h[8]:h[8]+h[9]];sh=struct.unpack_from('<16Q',scene);layer=scene[sh[12]:sh[12]+sh[13]];rgba=bytearray(153600)
 for y in range(160):
  owner=1 if h[5]==2 and y>=h[6] else 0;sky=raw[h[10+owner*2]:h[10+owner*2]+15192];ref=struct.unpack_from('<H',layer,20512+(y*25+24)*2)[0];palette=layer[28512+ref*4096:28512+ref*4096+512]
  for x in range(240):
   at=y*240+x;index=at-10560
   if 0<=index<15136:
    color=struct.unpack_from('<H',palette,sky[56+index]*2)[0]
    for c in range(3):v=color>>(c*5)&31;rgba[at*4+c]=(v<<3)|(v>>2)
    rgba[at*4+3]=255
 (out/f'sky-scene-{name}.rgba').write_bytes(rgba);fixtures[name]=dict(snapshot_sha256=hashlib.sha256(raw).hexdigest(),rgba_sha256=hashlib.sha256(rgba).hexdigest(),kind=h[5],split=h[6])
java=root/'work/android/java/org/codex/nfsugpreview';files=[java/(name+'.java') for name in ('NativeScenePacket','NativeSceneSnapshot','NativeSky','NativeSkyPlanes','NativeSkyScene')]+[root/'work/android/tests/org/codex/nfsugpreview/SkySceneTest.java'];jdk=Path(r'C:\NFSUG-Workspace\android-tools\jdk-21.0.12.1+1');classes=out/'sky-scene-classes';classes.mkdir(exist_ok=True);subprocess.run([str(jdk/'bin/javac.exe'),'--release','8','-d',str(classes),*map(str,files)],check=True);run=subprocess.run([str(jdk/'bin/java.exe'),'-cp',str(classes),'org.codex.nfsugpreview.SkySceneTest',str(out)],check=True,capture_output=True,text=True);print(run.stdout);report=dict(result='PASS_OWNED_SKY_SCENE_DECODE',java_stdout=run.stdout.strip(),fixtures=fixtures,source_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in files},android_runtime=False,gpu=False);(out/'sky-scene-host-report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
