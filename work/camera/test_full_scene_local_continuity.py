"""Local GPU motion measurements with complete retained scene and fixed HUD.

This isolates camera/UV sensitivity; scene membership and HUD timing are held
fixed deliberately, so it cannot prove whole-route continuity or scanout.
"""
from pathlib import Path
import csv, ctypes as C, json
import numpy as np
p=Path('work/camera').resolve()
class Point(C.Structure): _fields_=[('x',C.c_double),('y',C.c_double),('z',C.c_double)]
class Quaternion(C.Structure): _fields_=[(k,C.c_double) for k in ('x','y','z','w')]
class Pose(C.Structure): _fields_=[('position',Point),('rotation',Quaternion)]
sources=list(csv.DictReader((p/'uv-trigger-source-sources.csv').open()))
poses={(int(r['index']),int(r['role'])):Pose(Point(*[float(r[k]) for k in 'xyz']),Quaternion(*[float(r['q'+k]) for k in 'xyzw'])) for r in csv.DictReader((p/'uv-trigger-source-cameras.csv').open())}
d=C.CDLL(str(p/'road-transition-gpu-probe.dll'))
d.nf_road_transition_gpu_init.argtypes=[C.c_void_p,C.c_size_t,C.c_char_p]
d.nf_scene_transition_gpu_hud.argtypes=[C.c_void_p,C.c_size_t]
d.nf_scene_transition_gpu_render.argtypes=[C.c_void_p,C.c_double,C.c_int,C.c_void_p,C.c_void_p]
rgb=np.empty((2160,3840,3),np.uint8);depth=np.empty((2160,3840),np.float32)
records=[]
for i,source in enumerate(sources):
    packet=(p/f'uv-trigger-{i:03}.packet').read_bytes();owned=C.create_string_buffer(packet)
    assert d.nf_road_transition_gpu_init(owned,len(packet),str(p/'road-correction-reciprocal.bin').encode())==0
    try:
        hud=(p/f'uv-trigger-{i:03}.hud').read_bytes();hud_owned=C.create_string_buffer(hud)
        assert d.nf_scene_transition_gpu_hud(hud_owned,len(hud))
        camera=(Pose*2)(poses[i,0],poses[i,1]);alpha=float(source['alpha']);epsilon=1e-7
        assert epsilon<alpha<1-epsilon
        policies={}
        for mode in (0,2):
            assert d.nf_road_transition_gpu_uv_mode(mode)
            images=[];masks=[]
            for a in (alpha-epsilon,alpha,alpha+epsilon):
                assert d.nf_scene_transition_gpu_render(camera,a,1,rgb.ctypes.data,depth.ctypes.data)==0
                assert np.isfinite(depth).all() and np.any(depth>0)
                images.append(rgb.copy());masks.append(depth>0)
            delta=np.abs(images[0].astype(np.int16)-images[2].astype(np.int16))
            policies[str(mode)]=dict(changed_pixels=int(np.any(delta,axis=2).sum()),coverage_changed=int(np.count_nonzero(masks[0]!=masks[2])),maximum_channel_change=int(delta.max()),total_channel_change=int(delta.sum()))
        records.append(dict(index=i,target=float(source['target']),alpha_epsilon=epsilon,policies=policies))
    finally:d.nf_road_transition_gpu_close()
old_sources=list(csv.DictReader((p/'road-attribute-motion-sources.csv').open()))
old_poses={(int(r['index']),int(r['role'])):Pose(Point(*[float(r[k]) for k in 'xyz']),Quaternion(*[float(r['q'+k]) for k in 'xyzw'])) for r in csv.DictReader((p/'road-attribute-motion-cameras.csv').open())}
edge=next(r for r in csv.DictReader((p/'road-attribute-motion-edges.csv').open()) if int(r['index'])==9 and int(r['identity'])==10038408689761076994 and int(r['edge'])==1)
world=(Point*2)(*[Point(*[float(edge[f'world{n}'+k]) for k in 'xyz']) for n in (0,1)])
motion=C.CDLL(str(p/'visibility-probe-wide.dll'));sample=motion.nf_rigid_scene_sample
sample.argtypes=[C.c_void_p]*4+[C.c_double,C.c_void_p,C.c_uint,C.c_void_p]
segments={(int(r['older_refresh']),int(r['newer_refresh'])):(old_poses[i,0],old_poses[i,1]) for i,r in enumerate(old_sources)}
fixed=Pose(Point(0,0,0),Quaternion(0,0,0,1))
def pair_at(target):
    key=next(k for k in sorted(segments) if k[0]<=target<=k[1])
    return (Pose*2)(*segments[key]),(target-key[0])/(key[1]-key[0])
def front_depth(target):
    pair,a=pair_at(target);out=(Point*2)()
    assert sample(C.byref(pair[0]),C.byref(pair[1]),C.byref(fixed),C.byref(fixed),a,world,2,out)
    return out[1].z
lo=float(old_sources[9]['target']);hi=float(old_sources[10]['target'])
assert front_depth(lo)>64 and front_depth(hi)<64
for _ in range(45):
    mid=(lo+hi)/2
    if front_depth(mid)>64:lo=mid
    else:hi=mid
root=(lo+hi)/2;assert abs(front_depth(root)-64)<1e-8
packet=(p/'visibility-transition-009.packet').read_bytes();owned=C.create_string_buffer(packet)
assert d.nf_road_transition_gpu_init(owned,len(packet),str(p/'road-correction-reciprocal.bin').encode())==0
boundary=[]
try:
    hud=(p/'visibility-transition-009.hud').read_bytes();hud_owned=C.create_string_buffer(hud)
    assert d.nf_scene_transition_gpu_hud(hud_owned,len(hud))
    for mode in (0,2):
        assert d.nf_road_transition_gpu_uv_mode(mode)
        images=[];masks=[]
        for target in (root-1e-8,root+1e-8):
            camera,a=pair_at(target)
            assert d.nf_scene_transition_gpu_render(camera,a,1,rgb.ctypes.data,depth.ctypes.data)==0
            assert np.isfinite(depth).all()
            images.append(rgb.copy());masks.append(depth>0)
        delta=np.abs(images[0].astype(np.int16)-images[1].astype(np.int16))
        boundary.append(dict(mode=mode,changed_pixels=int(np.any(delta,axis=2).sum()),coverage_changed=int(np.count_nonzero(masks[0]!=masks[1])),total_channel_change=int(delta.sum())))
finally:d.nf_road_transition_gpu_close()
assert boundary[0]['changed_pixels']>0, 'Original-policy discontinuity control missing'
assert boundary[1]['changed_pixels']==0 and boundary[1]['coverage_changed']==0, 'Continuous-policy near-plane jump regressed'
report=dict(result='PASS',rendered_4K_cases=76,records=records,boundary_target=root,boundary=boundary,scope='Full-scene local sensitivity and recovered near-plane threshold sweep with fixed packet geometry/native bounds/owned HUD. Membership and HUD timing held fixed; not whole-route motion or smooth60fps proof.')
(p/'full-scene-local-continuity-tests.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
