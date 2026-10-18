from pathlib import Path
import struct,subprocess,json
root=Path(r'Y:\CODEX\NFSUG-Native-PC-Port');out=Path(r'C:\NFSUG-Workspace\NFSUG-android-source-background-local')
for name in ('whole','split'):
 raw=(out/f'race-background-{name}.nrb').read_bytes();h=struct.unpack_from('<16Q',raw);sky=raw[h[8]:h[8]+h[9]];sh=struct.unpack_from('<16Q',sky);nab=sky[sh[8]:sh[8]+sh[9]];nh=struct.unpack_from('<16Q',nab);layer=nab[nh[12]:nh[12]+nh[13]];rgba=bytearray(153600)
 for y in range(160):
  owner=int(h[5]==2 and y>=h[6]);bg=raw[h[10+owner*2]:h[10+owner*2]+76880];ref=struct.unpack_from('<H',layer,20512+(y*25+24)*2)[0]
  for x in range(240):
   p=y*240+x
   if bg[38480+p]:
    color=struct.unpack_from('<H',layer,28512+ref*4096+bg[80+p]*2)[0]
    for c in range(3):
     v=(color>>(c*5))&31;rgba[p*4+c]=(v<<3)|(v>>2)
    rgba[p*4+3]=255
 (out/f'background-{name}.rgba').write_bytes(rgba)
java=root/'work/android/java/org/codex/nfsugpreview';files=[java/(n+'.java') for n in ('NativeScenePacket','NativeSceneSnapshot','NativeSky','NativeSkyPlanes','NativeSkyScene','NativeBackgroundScene')]+[root/'work/android/tests/org/codex/nfsugpreview/BackgroundSceneTest.java'];jdk=Path(r'C:\NFSUG-Workspace\android-tools\jdk-21.0.12.1+1');classes=out/'background-classes';classes.mkdir(exist_ok=True)
subprocess.run([str(jdk/'bin/javac.exe'),'--release','8','-d',str(classes),*map(str,files)],check=True)
r=subprocess.run([str(jdk/'bin/java.exe'),'-cp',str(classes),'org.codex.nfsugpreview.BackgroundSceneTest',str(out)],check=True,capture_output=True,text=True);print(r.stdout);(out/'background-java-report.json').write_text(json.dumps(dict(result=r.stdout.strip(),android_runtime=False,gpu=False),indent=2))
