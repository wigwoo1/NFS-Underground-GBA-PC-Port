"""Check bounds pixel centers and ordered commands across supported packets."""
import argparse,hashlib,json,subprocess
from pathlib import Path
p=argparse.ArgumentParser()
for name in ('output','fixtures','jdk'):p.add_argument('--'+name,type=Path,required=True)
a=p.parse_args();source=Path(__file__).resolve().parent.parent;java=source/'java/org/codex/nfsugpreview';a.output.mkdir(parents=True,exist_ok=True)
names=['NativeScenePacket','NativeSceneSnapshot','NativeSceneComposition','NativeModelMesh','NativeWorldScene','NativeWorldMesh','NativeRoadCamera','NativeRoadProjection','NativeRoadAttributes','NativeRoadClip','NativeSceneDrawPlan','NativeLitWall','NativeWallLighting','NativeDrawBounds']
tests=['DrawBoundsTest','ScenePlanTest','SplitRowsTest'];files=[java/(n+'.java') for n in names]+[source/'tests/org/codex/nfsugpreview'/(n+'.java') for n in tests]
def run(command):
 r=subprocess.run([str(x) for x in command],capture_output=True,text=True);print(r.stdout,r.stderr);r.check_returncode();return r.stdout.strip()
run([a.jdk/'bin/javac.exe','--release','8','-encoding','UTF-8','-d',a.output,*files]);results={}
for name in tests:results[name]=run([a.jdk/'bin/java.exe','-cp',a.output,'org.codex.nfsugpreview.'+name,*([a.fixtures] if name=='ScenePlanTest' else [])])
assert results['SplitRowsTest'].startswith('PASS_SPLIT_ROWS ')
assert results['DrawBoundsTest'].startswith('PASS_DRAW_BOUNDS ') and results['ScenePlanTest'].startswith('PASS_SCENE_PLAN ')
(a.output/'bounds-host-report.json').write_text(json.dumps({'result':'PASS','tests':results,'source_sha256':{str(f.relative_to(source)):hashlib.sha256(f.read_bytes()).hexdigest() for f in files}},indent=2))
