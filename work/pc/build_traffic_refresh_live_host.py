"""Integrate only the fully verified exact-stage refresh candidate into a separate host."""
from pathlib import Path
import argparse,hashlib,json,shutil,subprocess,sys
source=Path(__file__).resolve().parent;base=Path(r'C:\NFSUG-Workspace');core=base/'NFSUG-pc-traffic-refresh-core'
parser=argparse.ArgumentParser();parser.add_argument('--output-dir',type=Path,default=base/'NFSUG-pc-traffic-refresh-live-tests');out=parser.parse_args().output_dir;sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
subprocess.run([sys.executable,str(source/'verify_traffic_refresh_milestone.py')],check=True)
f=json.loads((core/'traffic-refresh-build-report.json').read_text());t=json.loads((core/'traffic-refresh-core-test-report.json').read_text());m=json.loads((core/'traffic-refresh-milestone-report.json').read_text());assert m['late_route_failures']==0 and f['core_sha256']==t['core_sha256']==m['core_sha256']==sha(core/'capture-host.dll')
subprocess.run([sys.executable,str(source/'build_live_host.py'),'--reuse-scene','--source-transfer-core','--geometry-cache-core','--context-refresh-core','--output-dir',str(out)],check=True)
path=out/'live-build-report.json';r=json.loads(path.read_text());assert r['core_kind']=='guarded-model-context-refresh';(out/'baseline-live-build-report.json').write_text(json.dumps(r,indent=2));shutil.copy2(core/'capture-host.dll',out/'capture-host.dll')
r.update(core_kind='guarded-traffic-refresh-candidate',core_sha256=sha(out/'capture-host.dll'),baseline_core_kind='guarded-model-context-refresh',baseline_core_sha256=r['core_sha256'],traffic_core_parent_sha256=f['baseline_core_sha256'],core_factory_receipt_sha256=sha(core/'traffic-refresh-build-report.json'),core_parity_receipt_sha256=sha(core/'traffic-refresh-core-test-report.json'),core_milestone_receipt_sha256=sha(core/'traffic-refresh-milestone-report.json'),known_late_capture_misses_offscreen_route=0,live_integration_verified=False,full_scene_60fps=False)
r['source_sha256']['build_traffic_refresh_live_host.py']=sha(Path(__file__));path.write_text(json.dumps(r,indent=2));print('BUILT_REFRESH_LIVE_HOST_TESTS_PENDING',r['exe_sha256'],r['core_sha256'])
