"""Verify indexed uploads and scanline palettes, retaining unsupported scene gates."""
import argparse,hashlib,json,subprocess
from pathlib import Path
p=argparse.ArgumentParser()
for name in ('output','fixtures','sample','jdk'):p.add_argument('--'+name,type=Path,required=True)
a=p.parse_args();source=Path(__file__).resolve().parent.parent;java=source/'java/org/codex/nfsugpreview'
names=['NativeScenePacket','NativeSceneSnapshot','NativeModelMesh','NativeWorldScene','NativeWorldMesh','NativeRoadCamera','NativeRoadProjection','NativeRoadAttributes','NativeRoadClip','NativeSceneDrawPlan','NativeLitWall','NativeWallLighting','NativeDrawBounds','NativeHistoricalPalette']
files=[java/(name+'.java') for name in names]+[source/'tests/org/codex/nfsugpreview/IndexedMaterialTest.java']
a.output.mkdir(parents=True,exist_ok=True)
def run(command):
 r=subprocess.run([str(x) for x in command],capture_output=True,text=True);print(r.stdout,r.stderr);r.check_returncode();return r.stdout.strip()
run([a.jdk/'bin/javac.exe','--release','8','-encoding','UTF-8','-d',a.output,*files])
result=run([a.jdk/'bin/java.exe','-cp',a.output,'org.codex.nfsugpreview.IndexedMaterialTest',a.fixtures,a.sample]);assert result.startswith('PASS_INDEXED_MATERIAL ')
(a.output/'indexed-host-report.json').write_text(json.dumps({'result':'PASS','host':result,'gpu_indexed_runtime_verified':False,'source_sha256':{str(f.relative_to(source)):hashlib.sha256(f.read_bytes()).hexdigest() for f in files}},indent=2))
