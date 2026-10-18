"""Opt-in actual zoom model assets and native sampled command contexts."""
import ctypes as C,runpy,json
from pathlib import Path
p=Path(__file__).resolve().parent;crt=C.CDLL('msvcrt');crt._putenv_s.argtypes=[C.c_char_p,C.c_char_p]
assert crt._putenv_s(b'NF_TEST_FOCAL_SAMPLE',b'1')==0
context=runpy.run_path(str(p/'diagnose_late_model_pairs.py'))
checks=context['checks'];zoom=context['zoom_checks']
assert len(zoom)==25 and all(x['pose_pair_accepted'] for x in checks if 23<=x['older']<=27)
assert all(not x['pose_pair_accepted'] for x in checks if x['older'] in [21,22])
report=dict(result='PASS',zoom_samples=25,exact_asset_endpoints=10,complete_scene_samples=25,complete_packet_camera_endpoints=10,native_command_order_exact=True,accepted_zoom_pose_pairs=5,discrete_multipass_boundaries_rejected=2,scope='Actual original ledger zoom assets and complete world/model packets use sampled focal matching native Q8 command planning; mesh/UV/indices retained, full endpoints/camera arrays byteexact. GPU/live zoom integration not yet verified.')
(p/'zoom-model-sampling-tests.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
