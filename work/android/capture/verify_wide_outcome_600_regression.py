import hashlib,json,struct
from pathlib import Path
local=Path('C:/NFSUG-Workspace');narrow=local/'NFSUG-android-model-outcome-local';diagnostic=local/'NFSUG-android-visibility-rejection-local';wide=local/'NFSUG-android-wide-outcome-local'
def report(root):return json.loads((root/'600-frame-audit/enabled-report.json').read_text())
a,b,c=map(report,(narrow,diagnostic,wide))
assert b['source_packets']==a['source_packets']
by_a={r['serial']:r for r in a['source_packets']};by_c={r['serial']:r for r in c['source_packets']}
assert len(by_a)==145 and len(by_c)==148 and c['all_requested_endpoints_produced'] and c['failure_stages']=={}
assert all(by_c[k]==v for k,v in by_a.items())
restored=sorted(by_c.keys()-by_a.keys());assert restored==[17,18,19]
counts={};fixtures={}
for d in b['prerequisite_diagnostics']:
 if d['identity'][1] in restored:
  serial=d['identity'][1];row=d['visibility_rejection'];assert row[1]==7 and row[2]==0x03004d50 and row[8]==0x80000001 and row[9]==106 and row[11]==1
  raw=(diagnostic/f'original-{serial}.bin').read_bytes();counts[str(serial)]=struct.unpack_from('<H',raw,238)[0];assert counts[str(serial)]>20
  query=(diagnostic/f'query-{serial}.nqf').read_bytes();assert len(query)==295032 and struct.unpack_from('<I',query)[0]==0x3146514e
  fixtures[str(serial)]=dict(query_sha256=hashlib.sha256(query).hexdigest(),original_sha256=hashlib.sha256(raw).hexdigest())
assert counts=={'17':23,'18':21,'19':21}
for r in (a,b,c):
 assert r['original_frames']==600 and r['original_timing'] and r['audio_frames']==443007
 assert r['audio_sha256']=='eedce61302b062d825e9a26fa1d8399f0a7c29eaf4319e33a3d71eedd40be33e'
 assert r['source_scene_requests']==148
build=json.loads((wide/'owned-text-build-report.json').read_text());assert build['visibility_capacity']==64 and build['staged_only']
result=dict(result='PASS_WIDE_OWNED_ENDPOINT_600_REGRESSION',original_frames=600,original_timing=True,audio_frames=443007,audio_sha256=c['audio_sha256'],source_packets=148,requested=148,unchanged_previous_packets=145,restored_scene_serials=restored,original_queue_counts=counts,query_fixtures=fixtures,host_dll_sha256=build['library_sha256'],canonical_native_sources_changed=False,android_build_verified=False,live_renderer_verified=False)
(wide/'600-frame-audit/regression-report.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
