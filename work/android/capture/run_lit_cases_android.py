"""Run lit RGBA/state and indexed/state variants on the owned emulator."""
import argparse,json,shutil,subprocess,sys
from pathlib import Path
p=argparse.ArgumentParser()
for name in ('adb','build','fixtures'):p.add_argument('--'+name,type=Path,required=True)
a=p.parse_args();runner=Path(__file__).with_name('run_lit_gpu_android.py');reports={}
for case in ('rgba-lit','indexed-lit','indexed-lit-bounds'):
 subprocess.run([sys.executable,str(runner),'--adb',str(a.adb),'--build',str(a.build),'--sample',str(a.fixtures/(case+'.nab')),'--synthetic-fixture'],check=True)
 dest=a.build/case;dest.mkdir(exist_ok=True)
 for name in ('lit-scene-report.json','lit-scene-run.log','lit-scene-logcat.log','lit-scene-240.png','lit-scene-4k.png'):shutil.copy2(a.build/name,dest/name)
 reports[case]=json.loads((dest/'lit-scene-report.json').read_text())
(a.build/'lit-cases-android-report.json').write_text(json.dumps({'result':'PASS_ANDROID_LIT_MATERIAL_CASES','cases':reports},indent=2))
print('PASS_ANDROID_LIT_MATERIAL_CASES cases=3 formats=2 native_and_4k=true')
