"""Compile the existing live host and select the receipt-verified traffic candidate."""
from pathlib import Path
import argparse,hashlib,json,shutil,subprocess,sys
source=Path(__file__).resolve().parent;base=Path(r'C:\NFSUG-Workspace');out=base/'NFSUG-pc-traffic-live-host-tests';core=base/'NFSUG-pc-traffic-rotation-draw-camera-core'
parser=argparse.ArgumentParser();parser.add_argument('--output-dir',type=Path,default=out);out=parser.parse_args().output_dir
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
subprocess.run([sys.executable,str(source/'verify_traffic_rotation_milestone.py')],check=True)
factory=json.loads((core/'traffic-draw-camera-build-report.json').read_text());parity=json.loads((core/'traffic-draw-camera-core-test-report.json').read_text());milestone=json.loads((core/'traffic-draw-camera-milestone-report.json').read_text())
assert milestone['result']=='VERIFIED_PARTIAL_TRAFFIC_PRODUCER_RECOVERY' and milestone['after_late_capture_misses']==20
assert factory['core_sha256']==parity['core_sha256']==milestone['core_sha256']==sha(core/'capture-host.dll')
subprocess.run([sys.executable,str(source/'build_live_host.py'),'--reuse-scene','--source-transfer-core','--geometry-cache-core','--context-refresh-core','--output-dir',str(out)],check=True)
reportpath=out/'live-build-report.json';r=json.loads(reportpath.read_text());assert r['core_kind']=='guarded-model-context-refresh' and r['core_sha256']==factory['baseline_core_sha256']
(out/'baseline-live-build-report.json').write_text(json.dumps(r,indent=2));shutil.copy2(core/'capture-host.dll',out/'capture-host.dll')
r.update(core_kind='guarded-traffic-draw-camera-candidate',core_sha256=sha(out/'capture-host.dll'),baseline_core_kind='guarded-model-context-refresh',baseline_core_sha256=factory['baseline_core_sha256'],core_factory_receipt_sha256=sha(core/'traffic-draw-camera-build-report.json'),core_parity_receipt_sha256=sha(core/'traffic-draw-camera-core-test-report.json'),core_milestone_receipt_sha256=sha(core/'traffic-draw-camera-milestone-report.json'),known_late_capture_misses_offscreen_route=20,live_integration_verified=False,full_scene_60fps=False)
r['source_sha256']['build_traffic_live_host.py']=sha(Path(__file__));reportpath.write_text(json.dumps(r,indent=2));print('BUILT_TRAFFIC_LIVE_HOST_TESTS_PENDING',r['exe_sha256'],r['core_sha256'])
