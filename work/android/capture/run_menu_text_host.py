from pathlib import Path
import struct,subprocess,hashlib,json
root=Path(__file__).resolve().parents[1];out=Path(r'C:\NFSUG-Workspace\NFSUG-android-owned-text-local');jdk=Path(r'C:\NFSUG-Workspace\android-tools\jdk-21.0.12.1+1')
t=(out/'menu-4-positive.nft').read_bytes();p=(out/'menu-4-positive.nmp').read_bytes();expected=bytearray(153600)
assert struct.unpack_from('<QQ',t,24)==struct.unpack_from('<QQ',p,24)
for i,cov in enumerate(t[38480:]):
 if cov:
  color=struct.unpack_from('<H',p,40+(i//240)*512+t[80+i]*2)[0]
  expected[i*4:i*4+4]=bytes([((color>>(c*5)&31)*255//31) for c in range(3)]+[255])
# Hardware bit replication is the existing project's canonical BGR555 conversion.
for i,cov in enumerate(t[38480:]):
 if cov:
  color=struct.unpack_from('<H',p,40+(i//240)*512+t[80+i]*2)[0]
  for c in range(3):v=color>>(c*5)&31;expected[i*4+c]=(v<<3)|(v>>2)
(out/'menu-text.rgba').write_bytes(expected);classes=out/'menu-text-classes';classes.mkdir(exist_ok=True)
files=[root/'java/org/codex/nfsugpreview/NativeMenuText.java',root/'tests/org/codex/nfsugpreview/MenuTextTest.java']
subprocess.run([str(jdk/'bin/javac.exe'),'--release','8','-d',str(classes),*map(str,files)],check=True)
r=subprocess.run([str(jdk/'bin/java.exe'),'-cp',str(classes),'org.codex.nfsugpreview.MenuTextTest',str(out)],check=True,capture_output=True,text=True)
report=dict(result='PASS_HOST_MENU_TEXT_DECODE',java_stdout=r.stdout.strip(),fixture_sha256={n:hashlib.sha256((out/n).read_bytes()).hexdigest() for n in ('menu-4-positive.nft','menu-4-positive.nmp','menu-text.rgba','menu-4-positive.nmb')},source_sha256={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in files},android_runtime=False,gpu=False)
(out/'menu-text-decode-report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))

