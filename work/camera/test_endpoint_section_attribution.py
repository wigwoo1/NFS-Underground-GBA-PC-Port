"""Diagnostic-only validated section substitution to locate endpoint RGB change."""
from pathlib import Path
import ctypes as C,json,runpy,struct
import numpy as np
p=Path('work/camera').resolve()
context=runpy.run_path(str(p/'test_shared_scene_endpoint_gpu.py'))
gpu=context['d'];camera=context['camera'];rgb=context['rgb'];depth=context['depth']
baseline=context['images']['left-near',5,1];target=context['images']['right-near',5,1]
class Section(C.Structure):_fields_=[('data',C.c_void_p),('size',C.c_size_t)]
class Packet(C.Structure):_fields_=[('serial',C.c_uint),('begin',C.c_uint),('end',C.c_uint),('page',C.c_uint),('sections',Section*5)]
bridge=C.CDLL(str(p/'visibility-probe-wide.dll'))
bridge.nf_scene_packet_view.argtypes=[C.c_void_p,C.c_size_t,C.POINTER(Packet)]
bridge.nf_scene_packet_build.argtypes=[C.POINTER(Packet),C.POINTER(C.c_void_p),C.POINTER(C.c_size_t)]
bridge.nf_scene_packet_free.argtypes=[C.c_void_p]
owners=[];views=[]
for name in ('left-near','right-near'):
    data=(p/f'shared-endpoint-{name}.packet').read_bytes();owners.append(C.create_string_buffer(data));view=Packet()
    assert bridge.nf_scene_packet_view(owners[-1],len(data),C.byref(view));views.append(view)
records=[]
def differences(a,b):return sum(x!=y for x,y in zip(a,b))+abs(len(a)-len(b))
for index,name in enumerate(('model','world','order','lighting','identity_bounds')):
    a,b=views[0].sections[index],views[1].sections[index]
    left=C.string_at(a.data,a.size);right=C.string_at(b.data,b.size)
    record=dict(section=name,left_bytes=len(left),right_bytes=len(right),same_bytes=left==right,
                changed_bytes=sum(x!=y for x,y in zip(left,right))+abs(len(left)-len(right)))
    if name=='model':
        h=struct.unpack_from('<6I',left);assert h==struct.unpack_from('<6I',right)
        _,vertices,faces,corners,width,height=h
        points=160+vertices*24;uv=points+faces+corners*2;tex=uv+corners*16;end=tex+width*height*4
        record['component_changed_bytes']=dict(header=differences(left[:160],right[:160]),vertices=differences(left[160:points],right[160:points]),faces_indices=differences(left[points:uv],right[points:uv]),uv=differences(left[uv:tex],right[uv:tex]),texture_rgba=differences(left[tex:end],right[tex:end]),indices_trailer=differences(left[end:],right[end:]))
    if name=='world':
        count=struct.unpack_from('<I',left,4)[0];assert count==struct.unpack_from('<I',right,4)[0]
        pos=8;surfaces=[]
        for ring in range(count):
            n,w,h=struct.unpack_from('<3I',left,pos);assert (n,w,h)==struct.unpack_from('<3I',right,pos)
            start=pos+12;uv=start+n*24;tex=uv+n*16;end=tex+w*h*4
            surfaces.append(dict(ring=ring,xyz=differences(left[start:uv],right[start:uv]),uv=differences(left[uv:tex],right[uv:tex]),texture_rgba=differences(left[tex:end],right[tex:end])))
            pos=end
        record['surfaces']=surfaces;record['metadata_changed_bytes']=differences(left[pos:],right[pos:])
    candidate=Packet();C.memmove(C.byref(candidate),C.byref(views[0]),C.sizeof(Packet))
    candidate.sections[index]=b
    out=C.c_void_p();size=C.c_size_t()
    assert bridge.nf_scene_packet_build(C.byref(candidate),C.byref(out),C.byref(size)),name
    try:packet=C.string_at(out,size.value)
    finally:bridge.nf_scene_packet_free(out)
    owned=C.create_string_buffer(packet)
    assert gpu.nf_road_transition_gpu_init(owned,len(packet),str(p/'road-correction-reciprocal.bin').encode())==0
    try:
        hud=(p/'moving-transition-005.hud').read_bytes();hud_owned=C.create_string_buffer(hud)
        assert gpu.nf_scene_transition_gpu_hud(hud_owned,len(hud)) and gpu.nf_road_transition_gpu_uv_mode(2)
        result=gpu.nf_scene_transition_gpu_render(camera,0,1,rgb.ctypes.data,depth.ctypes.data)
        assert result==0,(name,result)
        assert np.isfinite(depth).all()
        record.update(changed_pixels_from_left=int(np.any(rgb!=baseline,axis=2).sum()),remaining_pixels_from_right=int(np.any(rgb!=target,axis=2).sum()))
    finally:gpu.nf_road_transition_gpu_close()
    records.append(record)
report=dict(result='PASS',diagnostic_section_renders=5,records=records,
            scope='Validated diagnostic section substitution between regenerated near-limit packets at pinned camera/HUD. Hybrid packets are attribution tools only, not production policy or original fidelity proof.')
(p/'endpoint-section-attribution-tests.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
