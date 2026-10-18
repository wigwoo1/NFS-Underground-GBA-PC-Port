"""Bind the offscreen geometry recovery and maintained/live integration evidence."""
from pathlib import Path
import hashlib,json
source=Path(__file__).resolve().parent;base=Path(r'C:\NFSUG-Workspace');candidate=base/'NFSUG-pc-empty-model-plane-tests';live=base/'NFSUG-pc-empty-plane-live-host-tests'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
paths={'candidate':candidate/'empty-plane-build-report.json','gpu':candidate/'empty-plane-test-report.json','second':candidate/'second-frame-test-report.json','route':base/'NFSUG-pc-empty-model-plane-route-tests/diverse-route-report.json','scene':base/'NFSUG-pc-scene-tests/scene-build-report.json','build':live/'live-build-report.json','regression':live/'live-test-report.json','live':live/'traffic-live-route-test-report.json'}
# The candidate GPU receipt name is read from its test recipe to avoid ambiguous files.
if not paths['gpu'].exists():
 matches=[x for x in candidate.glob('*report.json') if json.loads(x.read_text()).get('result')=='PASS_EMPTY_AXIS_MODEL_PLANE_SAVED_FRAME_AND_GPU'];assert len(matches)==1;paths['gpu']=matches[0]
r={k:json.loads(p.read_text()) for k,p in paths.items()}
assert (source/'source_scene.c').read_bytes()==(candidate/'source_scene_empty_plane.c').read_bytes()
assert r['candidate']['helper_sha256']==sha(source/'empty_model_plane.h')
assert sha(source/'model_mesh.c')==r['candidate']['source_sha256']['model_mesh.c']
assert r['route']['result']=='VERIFIED_EMPTY_MODEL_PLANE_FULL_ROUTE_RECOVERY' and r['route']['baseline_prepared']==5807 and r['route']['candidate_prepared']==5970
assert r['route']['all6000_original_pixels_exact'] and r['route']['original_clocks_exact'] and r['route']['allocation_lifetimes_balanced']
assert r['second']['result']=='PASS_REPEATED_VERTEX_FULL_FRAME_RECOVERY' and r['second']['unchanged_source_vertices']
for n,h in r['scene']['source_sha256'].items():assert sha(source/n)==h,n
for n,h in r['build']['source_sha256'].items():assert sha(source/n)==h,n
assert r['build']['exe_sha256']==r['regression']['exe_sha256']==r['live']['exe_sha256']==sha(live/'NFSUG-Source-Native-Preview.exe')
assert r['live']['session']['prepare_failures']==0 and r['live']['audio_pcm_exact']
assert r['live']['build_receipt_sha256']==sha(paths['build']) and r['live']['regression_receipt_sha256']==sha(paths['regression'])
report=dict(result='VERIFIED_EMPTY_MODEL_PLANE_RECOVERY_LIVE_LIMITS_OPEN',recovered_preparation_failures_offscreen=163,available_source_frames=5970,original_steps=6000,previously_working_commands_exact=r['route']['working_commands_exact'],previously_working_vertex_plane_bytes_exact=r['route']['working_vertex_plane_bytes_exact'],live_prepare_failures=0,live_elapsed_seconds=r['live']['session']['elapsed_seconds'],original_wall_clock_budget_met=r['live']['original_wall_clock_budget_met'],sampled_audio_queue_empty_observed=r['live']['sampled_audio_queue_empty_observed'],known_late_source_gaps=20,full_scene_60fps=False,rough_project_percent=70,receipts={k:dict(path=str(p),sha256=sha(p)) for k,p in paths.items()},source_sha256={n:sha(source/n) for n in ['source_scene.c','empty_model_plane.h','model_mesh.c','build_source_scene.py','build_traffic_live_host.py','test_traffic_live_route.py','verify_empty_model_plane_milestone.py']},next_dependency='Resolve independently diagnosed one-refresh traffic producer gaps, then verify full-scene motion, audio on the Intel PC and physical controller behavior. Do not infer 60fps from presents.')
(live/'empty-model-plane-milestone-report.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k not in ['receipts','source_sha256']},indent=2))
