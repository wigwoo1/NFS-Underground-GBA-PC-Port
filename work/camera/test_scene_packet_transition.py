"""Compare adjacent generated scenes with a common camera and pinned HUD.

Packets still contain their own sampled object poses, materials and lighting.
This is controlled attribution, not a reconstructed common-time scene.
"""
from pathlib import Path
import csv,ctypes as C,json
import numpy as np
p=Path('work/camera').resolve()
class Point(C.Structure):_fields_=[(k,C.c_double) for k in 'xyz']
class Quaternion(C.Structure):_fields_=[(k,C.c_double) for k in 'xyzw']
class Pose(C.Structure):_fields_=[('position',Point),('rotation',Quaternion)]
poses={(int(r['index']),int(r['role'])):Pose(Point(*[float(r[k]) for k in 'xyz']),Quaternion(*[float(r['q'+k]) for k in 'xyzw'])) for r in csv.DictReader((p/'moving-transition-source-cameras.csv').open())}
sources=list(csv.DictReader((p/'moving-transition-source-sources.csv').open()))
assert sources[5]['newer']==sources[6]['older']
# Both source pairs have exactly the same recovered camera at their shared tick.
assert bytes(poses[5,1])==bytes(poses[6,0])
camera=(Pose*2)(poses[5,1],poses[5,1])
d=C.CDLL(str(p/'road-transition-gpu-probe.dll'))
d.nf_road_transition_gpu_init.argtypes=[C.c_void_p,C.c_size_t,C.c_char_p]
d.nf_scene_transition_gpu_hud.argtypes=[C.c_void_p,C.c_size_t]
d.nf_scene_transition_gpu_render.argtypes=[C.c_void_p,C.c_double,C.c_int,C.c_void_p,C.c_void_p]
rgb=np.empty((2160,3840,3),np.uint8);depth=np.empty((2160,3840),np.float32)
images={};masks={}
for index in (5,6):
    data=(p/f'moving-transition-{index:03}.packet').read_bytes();owned=C.create_string_buffer(data)
    assert d.nf_road_transition_gpu_init(owned,len(data),str(p/'road-correction-reciprocal.bin').encode())==0
    try:
        assert d.nf_road_transition_gpu_uv_mode(2)
        for hud_index in (5,6):
            hud=(p/f'moving-transition-{hud_index:03}.hud').read_bytes();hud_owned=C.create_string_buffer(hud)
            assert d.nf_scene_transition_gpu_hud(hud_owned,len(hud))
            for bounds in (0,1):
                assert d.nf_scene_transition_gpu_render(camera,0,bounds,rgb.ctypes.data,depth.ctypes.data)==0
                assert np.isfinite(depth).all() and np.any(depth>0)
                images[index,hud_index,bounds]=rgb.copy();masks[index,hud_index,bounds]=depth>0
    finally:d.nf_road_transition_gpu_close()
def compare(left,right):
    delta=np.abs(images[left].astype(np.int16)-images[right].astype(np.int16))
    return dict(changed_pixels=int(np.any(delta,axis=2).sum()),mean_absolute_channel_change=float(delta.mean()),coverage_changed=int(np.count_nonzero(masks[left]!=masks[right])))
report=dict(result='PASS',rendered_4K_cases=8,common_camera_refresh=int(sources[5]['newer_refresh']),
            packet_change_fixed_hud={str(b):compare((5,5,b),(6,5,b)) for b in (0,1)},
            hud_change_fixed_packet={str(i):compare((i,5,1),(i,6,1)) for i in (5,6)},
            bounds_change_fixed_packet={str(i):compare((i,5,0),(i,5,1)) for i in (5,6)},
            scope='Shared original boundary camera and pinned exact HUD isolate camera/HUD effects. Generated packets still have different sampled object pose,geometry,membership,materials,lighting and bounds; not common-time scene regeneration or continuity proof.')
(p/'scene-packet-transition-tests.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
