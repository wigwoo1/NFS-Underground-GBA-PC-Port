import hashlib,json
from pathlib import Path
local=Path('C:/NFSUG-Workspace');base=local/'NFSUG-android-wide-outcome-local';shared=local/'NFSUG-android-shared-outcome-local';native=local/'NFSUG-android-shared-wide-native-local'
a=json.loads((base/'600-frame-audit/enabled-report.json').read_text());b=json.loads((shared/'600-frame-audit/enabled-report.json').read_text());assert b['source_packets']==a['source_packets'];assert len(b['source_packets'])==148 and b['failure_stages']=={}
assert b['original_frames']==600 and b['original_timing'] and b['audio_frames']==443007 and b['audio_sha256']==a['audio_sha256']
off=json.loads((shared/'600-frame-audit/disabled-report.json').read_text());assert len(off['source_packets'])==142 and off['failure_stages']=={'4':6}
assert off['original_frames']==600 and off['original_timing'] and off['audio_frames']==443007 and off['audio_sha256']==b['audio_sha256']
by_on={r['serial']:r for r in b['source_packets']};assert all(by_on[r['serial']]==r for r in off['source_packets'])
canonical=Path('Y:/CODEX/NFSUG-Native-PC-Port/work')
for name in ('camera/model_outcome.h','camera/native_surface.h','camera/live_scene.h','camera/live_visibility.h','camera/live_model_inputs_api.h','camera/scene_assembly.c'):
 expected=hashlib.sha256((canonical/name).read_bytes()).hexdigest()
 for cache in (shared,native):
  provenance=json.loads((cache/'source-provenance.json').read_text());assert provenance['unaltered_source_sha256'][name]==expected
host=json.loads((shared/'owned-text-build-report.json').read_text());assert not any(k.startswith('staged_model_outcome_') for k in host['extension_sha256'])
android=json.loads((native/'capture-jni-build-report.json').read_text());assert android['result']=='PASS_ANDROID_BORROWED_CAPTURE_BUILD' and android['jni'] and android['visibility_capacity']==64
assert {t['abi'] for t in android['targets']}=={'x86_64','arm64-v8a'}
for t in android['targets']:assert not t['legacy_speed_apis_exported'] and min(t['load_alignments'])>=16384
result=dict(result='PASS_SHARED_MODEL_OUTCOME_600_AND_ANDROID_BUILD',original_frames=600,original_timing=True,audio_frames=b['audio_frames'],audio_sha256=b['audio_sha256'],source_packets=148,disabled_packets=142,all_142_disabled_packets_unchanged=True,shared_source_provenance_verified=True,all_148_packets_byte_identical_to_experiment=True,host_only_producer_patch=False,host_dll_sha256=host['library_sha256'],android_targets=android['targets'],android_runtime_tested=False,live_renderer_tested=False,interpolated_no_draw_supported=False)
(shared/'600-frame-audit/shared-integration-report.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
