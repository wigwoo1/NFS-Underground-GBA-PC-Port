"""Verify the final traffic producer milestone without claiming a complete port."""
from pathlib import Path
import hashlib,json
source=Path(__file__).resolve().parent;base=Path(r'C:\NFSUG-Workspace');out=base/'NFSUG-pc-traffic-rotation-draw-camera-core'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
buildpath=out/'traffic-draw-camera-build-report.json';build=json.loads(buildpath.read_text());assert build['core_sha256']==sha(out/'capture-host.dll')
for n,h in build['maintained_source_sha256'].items():assert sha(source/n)==h,n
for n,h in build['staged_input_sha256'].items():assert sha(out/'source'/n)==h,n
assert build['script_sha256']==sha(source/'build_traffic_rotation_draw_core.py')
paths=[out/'traffic-draw-camera-core-test-report.json',base/'NFSUG-pc-traffic-rotation-draw-helper-tests/traffic-helper-test-report.json',base/'NFSUG-pc-traffic-rotation-draw-camera-route-tests/diverse-route-report.json',base/'NFSUG-pc-traffic-rotation-draw-model-tests/diverse-route-report.json']
parity,helper,route,model=[json.loads(p.read_text()) for p in paths]
assert parity['result']=='PASS_TRAFFIC_DRAW_CAMERA_CORE_PARITY' and parity['core_sha256']==build['core_sha256']
assert parity['all_original_pixels_exact'] and parity['all_complete_source_bytes_exact'] and parity['transfers_balanced']
assert helper['result']=='PASS_GUARDED_TRAFFIC_DRAW_CAMERA_HELPERS' and helper['core_build_sha256']==sha(buildpath)
assert route['result']=='VERIFIED_TRAFFIC_DRAW_CAMERA_ROUTE_ORIGINAL_OUTPUT_PARITY' and route['core_sha256']==build['core_sha256'] and route['steps']==6000
assert route['all6000_original_pixels_exact'] and route['original_clocks_exact'] and route['allocation_lifetimes_balanced']
assert route['audio_frames']==4430117 and route['audio_sha256']=='e3d0620b037591b5e4d2fb1e806448e2635eb056d614dd3710942a3c6b645807'
assert route['complete_source_frames']==5970 and len(route['failures'])==30
assert [x['step'] for x in route['failures'][:10]]==list(range(1,11))
late=[x['step'] for x in route['failures'][10:]];assert late==list(range(3610,3615))+list(range(3667,3671))+list(range(4462,4467))+list(range(5204,5210))
assert route['traffic_rotation_stats'][1:5]==[417,798,10,0]
assert model['result']=='VERIFIED_RECOVERED_TRAFFIC_MODEL_POSE' and model['core_sha256']==build['core_sha256'] and model['target_models']
assert all(x['scene']==848 and x['identity'][2]==0x02005834 and x['absolute_quaternion_dot']>1-1e-7 for x in model['target_models'])
for report,script in [(parity,'test_traffic_rotation_draw_core.py'),(helper,'test_traffic_rotation_draw_helpers.py'),(route,'test_traffic_rotation_draw_route.py'),(model,'test_traffic_rotation_draw_model.py')]:assert report.get('maintained_test_sha256',report.get('script_sha256'))==sha(source/script),script
old=json.loads((base/'NFSUG-pc-diverse-route-tests/diverse-route-report.json').read_text());assert len(old['failures'])==809
first=json.loads((base/'NFSUG-pc-traffic-rotation-route-tests/diverse-route-report.json').read_text());assert len(first['failures'])==809
reason=json.loads((base/'NFSUG-pc-traffic-rotation-guard-core/traffic-guard-probe-report.json').read_text());d=reason['detail']
assert d[5]==848 and d[6]==d[8]==0x02005834 and d[7]==d[9]==0x03005ec0 and d[10]==d[11]==2 and d[12]==848
assert d[32:41]!=d[48:57] and d[64:73]==d[80:89]
report=dict(result='VERIFIED_PARTIAL_TRAFFIC_PRODUCER_RECOVERY',core_sha256=build['core_sha256'],before_late_capture_misses=799,after_late_capture_misses=20,late_misses_resolved=779,remaining_intervals=[[3610,3614],[3667,3670],[4462,4466],[5204,5209]],original6000_pixels_audio_clocks_exact=True,former_failed_traffic_model_present_with_expected_pose=True,first_attempt_preserved_output_but_no_gap_reduction=True,second_attempt_binds_actual_draw_camera=True,full_scene_60fps=False,live_integration_verified=False,playable_package_changed=False,rough_project_percent=69,next_dependency='Stop speculative fixes after two focused candidates. Sol Medium should freeze the first remaining gap at3610 and distinguish producer refresh-crossing from a different source failure, then verify and integrate the candidate into the live host.',limits='5990 post-startup source opportunities contain20 misses; 5970/6000 total captures. This is offscreen scripted-route coverage, not lap completion, full-race fidelity, or smooth60 gameplay. Recovered Q14 pose is normalized/rounded, with tested recomposition residual up to4 Q14 units; no new traffic pixel-exact 4K claim.',evidence_sha256={str(p):sha(p) for p in paths+[buildpath,base/'NFSUG-pc-traffic-rotation-route-tests/diverse-route-report.json',base/'NFSUG-pc-traffic-rotation-guard-core/traffic-guard-probe-report.json',base/'NFSUG-pc-rotation-trace-v4-core/rotation-trace-v4-core-test-report.json',base/'NFSUG-pc-rotation-trace-v4-core/probe/rotation-events.json']},script_sha256=sha(Path(__file__)))
(out/'traffic-draw-camera-milestone-report.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='evidence_sha256'},indent=2))
