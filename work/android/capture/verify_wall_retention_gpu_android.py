"""Join current renderer sources, APK/native build receipts and two real GPU runs."""
from pathlib import Path
import json,hashlib,zipfile
base=Path(r'C:\NFSUG-Workspace');root=Path(r'Y:\CODEX\NFSUG-Native-PC-Port');build=base/'NFSUG-android-local/app-wall-retention-gpu-tests';native=base/'NFSUG-android-exact-wall-native-local'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
apk=json.loads((build/'apk-build-report.json').read_text());assert sha(Path(apk['apk']))==apk['sha256'];checked=0
for name,digest in apk['source_sha256'].items():assert sha(root/'work/android'/name)==digest,name;checked+=1
provenance=json.loads((native/'source-provenance.json').read_text())
for name,digest in provenance['unaltered_source_sha256'].items():assert sha(root/('outputs/nfsug-research' if name in ('native_span.c','native_span.h') else 'work')/name)==digest,name
nr=json.loads((native/'capture-jni-build-report.json').read_text())
with zipfile.ZipFile(apk['apk']) as z:
 for target in nr['targets']:assert hashlib.sha256(z.read('lib/'+target['abi']+'/libnfsug_android_core.so')).hexdigest()==target['sha256']
reports={}
for scope,expected in [('restored',9),('sequence',49)]:
 report=json.loads((build/(scope+'-verified-report.json')).read_text());assert report['snapshots']==expected and report['coverage_holes']==0 and report['context_recreated'] and report['four_k_checks']>=2 and report['apk_sha256']==apk['sha256']
 folder=base/('NFSUG-wall-retention-gpu-fixtures' if scope=='restored' else 'NFSUG-android-source-road-sequence-local')
 for name,digest in report['fixtures'].items():assert sha(folder/name)==digest,name
 reports[scope]={k:report[k] for k in ('snapshots','coverage_checks','coverage_holes','wall_source_color_checks','retained_source_color_checks','pixel_checks','four_k_checks','context_recreated','real_time_pacing')}
result=dict(result='PASS_WALL_RETENTION_GPU_INTEGRATION',java_and_instrumentation_sources=checked,apk_sha256=apk['sha256'],scopes=reports,live_gameplay_tested=False,physical_arm64_tested=False)
(build/'wall-gpu-integration-report.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))

