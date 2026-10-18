"""Execute both synthetic clipping formats through the owned indexed GPU runner."""
import argparse,json,shutil,subprocess,sys
from pathlib import Path
p=argparse.ArgumentParser()
for name in ('adb','build','fixtures'):p.add_argument('--'+name,type=Path,required=True)
a=p.parse_args();runner=Path(__file__).with_name('run_indexed_gpu_android.py');reports={}
for case in ('world-only','world-model'):
 subprocess.run([sys.executable,str(runner),'--adb',str(a.adb),'--build',str(a.build),'--sample',str(a.fixtures/(case+'.nab')),'--synthetic-fixture'],check=True)
 dest=a.build/case;dest.mkdir(exist_ok=True)
 for name in ('indexed-scene-report.json','indexed-scene-run.log','indexed-scene-logcat.log','indexed-scene-240.png','indexed-scene-4k.png'):shutil.copy2(a.build/name,dest/name)
 reports[case]=json.loads((dest/'indexed-scene-report.json').read_text())
(a.build/'bounds-android-report.json').write_text(json.dumps({'result':'PASS_ANDROID_DRAW_BOUNDS','cases':reports},indent=2))
print('PASS_ANDROID_DRAW_BOUNDS formats=2 native_and_4k=true')
