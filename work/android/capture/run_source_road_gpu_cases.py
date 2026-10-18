"""Run only owned AVD raw-camera GPU cases with C-parity source provenance."""
from pathlib import Path
import argparse,hashlib,json,shutil,subprocess,sys
p=argparse.ArgumentParser()
for n in ('adb','build','fixtures','mesh_report'):p.add_argument('--'+n.replace('_','-'),type=Path,required=True)
a=p.parse_args();build=json.loads((a.build/'apk-build-report.json').read_text());mesh=json.loads(a.mesh_report.read_text());assert mesh['result']=='PASS_SOURCE_WORLD_MESH_C_PARITY'
for name,digest in mesh['source_sha256'].items():
 if name.startswith('java'):assert build['source_sha256'][name.replace('\\','/')]==digest,'Stale C-parity helper '+name
manifest=json.loads((a.fixtures/'fixture-manifest.json').read_text());reports={}
for name,fixture in manifest.items():
 assert fixture['geometry_sections_identical_to_c_parity_fixture'];sample=a.fixtures/name;assert hashlib.sha256(sample.read_bytes()).hexdigest()==fixture['sha256']
 subprocess.run([sys.executable,str(Path(__file__).with_name('run_source_road_gpu_android.py')),'--adb',str(a.adb),'--build',str(a.build),'--sample',str(sample),'--synthetic-fixture'],check=True)
 report=json.loads((a.build/'source-road-scene-report.json').read_text());assert report['near_crossing_edges']==fixture['expected_near_crossing_edges'] and report['visible_corrected_road_sample_evaluations']>0
 destination=a.build/sample.stem;destination.mkdir(exist_ok=True)
 for artifact in ('source-road-scene-report.json','source-road-scene-run.log','source-road-scene-logcat.log','source-road-scene-240.png','source-road-scene-4k.png'):shutil.copy2(a.build/artifact,destination/artifact)
 reports[sample.stem]=report
(a.build/'source-road-gpu-cases-report.json').write_text(json.dumps({'result':'PASS_ANDROID_SOURCE_ROAD_GPU_CASES','cases':reports,'pixel_comparisons':sum(r['source_pixel_checks'] for r in reports.values()),'visible_road_sample_evaluations':sum(r['visible_corrected_road_sample_evaluations'] for r in reports.values()),'scope':'Synthetic raw-camera endpoint roads, native/4K offscreen and context recreation; no live timing claim'},indent=2));print('All raw-camera GPU cases PASS',flush=True)
