"""Run captured split and explicit owner-color sentinels on the owned AVD."""
from pathlib import Path
import argparse,hashlib,json,shutil,subprocess,sys
p=argparse.ArgumentParser()
for n in ('adb','build','fixtures','host_report'):p.add_argument('--'+n.replace('_','-'),type=Path,required=True)
a=p.parse_args();build=json.loads((a.build/'apk-build-report.json').read_text());host=json.loads(a.host_report.read_text());assert host['result']=='PASS' and host['tests']['SplitRowsTest'].startswith('PASS_SPLIT_ROWS ')
for name,digest in host['source_sha256'].items():
 if name.startswith('java'):assert build['source_sha256'][name.replace('\\','/')]==digest,'Stale row composition helper '+name
manifest=json.loads((a.fixtures/'fixture-manifest.json').read_text());reports={}
for name,fixture in manifest.items():
 sample=a.fixtures/name;assert hashlib.sha256(sample.read_bytes()).hexdigest()==fixture['sha256'];command=[sys.executable,str(Path(__file__).with_name('run_split_scene_gpu_android.py')),'--adb',str(a.adb),'--build',str(a.build),'--sample',str(sample)]
 if fixture['synthetic_sentinel']:command.append('--synthetic-fixture')
 subprocess.run(command,check=True);report=json.loads((a.build/'split-scene-report.json').read_text());assert report['split_row']==fixture['split_row'] and report['synthetic_sentinel']==fixture['synthetic_sentinel']
 if fixture['synthetic_sentinel']:assert report['exact_owner_row_checks']>=2480 and report['owner0_exact_rows']>0 and report['owner1_exact_rows']>0
 else:assert report['owner0_visible_sample_evaluations']>0 and report['owner1_visible_sample_evaluations']>0
 destination=a.build/sample.stem;destination.mkdir(exist_ok=True)
 for artifact in ('split-scene-report.json','split-scene-run.log','split-scene-logcat.log','split-scene-240.png','split-scene-4k.png'):shutil.copy2(a.build/artifact,destination/artifact)
 reports[sample.stem]=report
(a.build/'split-scene-cases-report.json').write_text(json.dumps({'result':'PASS_ANDROID_SPLIT_SCENE_CASES','cases':reports,'pixel_comparisons':sum(r['source_pixel_checks'] for r in reports.values()),'exact_owner_row_checks':sum(r['exact_owner_row_checks'] for r in reports.values()),'scope':'Offscreen retained split geometry plus synthetic ownership sentinels; no live full-scene timing claim'},indent=2));print('Captured split and all owner sentinel cases PASS',flush=True)
