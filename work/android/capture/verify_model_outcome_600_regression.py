import json
from pathlib import Path
base=Path('C:/NFSUG-Workspace/NFSUG-android-model-outcome-local/600-frame-audit')
on=json.loads((base/'enabled-report.json').read_text());off=json.loads((base/'disabled-report.json').read_text())
for r in (on,off):
 assert r['original_frames']==600 and r['original_timing']
 assert r['audio_frames']==443007 and r['audio_sha256']=='eedce61302b062d825e9a26fa1d8399f0a7c29eaf4319e33a3d71eedd40be33e'
 assert r['source_scene_requests']==148
by_on={r['serial']:r for r in on['source_packets']};by_off={r['serial']:r for r in off['source_packets']}
assert len(by_on)==145 and len(by_off)==139
assert all(by_on[k]==v for k,v in by_off.items())
restored=sorted(by_on.keys()-by_off.keys());assert len(restored)==6 and 7 in restored
missing=sorted(set(range(148))-by_on.keys());assert missing==[17,18,19]
assert on['failure_stages']=={'1':3} and off['failure_stages']=={'4':6,'1':3}
for d in on['prerequisite_diagnostics']:
 if d['identity'][1] in missing:
  assert not d['model_inputs_valid'] and not d['source_audit'] and not d['render_snapshot'] and not d['visibility_pose']
report=dict(result='PASS_600_FRAME_CONTROLLED_MODEL_OUTCOME_REGRESSION',original_framebuffers=600,original_timing=True,audio_stereo_frames=443007,audio_sha256=on['audio_sha256'],requested_scene_owners=148,enabled_packets=145,disabled_packets=139,unchanged_packets=139,restored_scene_serials=restored,remaining_missing_serials=missing,remaining_failure='Source snapshot/model ownership unavailable before assembly; exact capture rejection site not instrumented',live_renderer_verified=False)
(base/'regression-report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
