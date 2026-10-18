"""Verify every uploaded lit variant against original plane/state payloads."""
import argparse,hashlib,json,subprocess
from pathlib import Path
p=argparse.ArgumentParser()
for name in ('output','fixtures','jdk'):p.add_argument('--'+name,type=Path,required=True)
a=p.parse_args();source=Path(__file__).resolve().parent.parent;java=source/'java/org/codex/nfsugpreview';a.output.mkdir(parents=True,exist_ok=True)
names=['NativeScenePacket','NativeSceneSnapshot','NativeModelMesh','NativeWorldScene','NativeWorldMesh','NativeRoadCamera','NativeRoadProjection','NativeRoadAttributes','NativeRoadClip','NativeSceneDrawPlan','NativeDrawBounds','NativeLitWall','NativeWallLighting'];files=[java/(n+'.java') for n in names]+[source/'tests/org/codex/nfsugpreview/LitWallMaterialTest.java']
def run(command):
 r=subprocess.run([str(x) for x in command],capture_output=True,text=True);print(r.stdout,r.stderr);r.check_returncode();return r.stdout.strip()
run([a.jdk/'bin/javac.exe','--release','8','-encoding','UTF-8','-d',a.output,*files]);result=run([a.jdk/'bin/java.exe','-cp',a.output,'org.codex.nfsugpreview.LitWallMaterialTest',a.fixtures]);assert result.startswith('PASS_LIT_WALL_MATERIAL ')
(a.output/'lit-material-host-report.json').write_text(json.dumps({'result':'PASS','host':result,'source_sha256':{str(f.relative_to(source)):hashlib.sha256(f.read_bytes()).hexdigest() for f in files},'gpu_lit_runtime_verified':False},indent=2))
