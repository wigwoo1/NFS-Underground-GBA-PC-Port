"""Regenerate adjacent original source pairs at their shared endpoint."""
from pathlib import Path
import ctypes as C, struct, os, json, hashlib
p=Path('work/camera').resolve();rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba')
assert os.environ.get('NF_LIVE_ROAD_ATTRIBUTES')=='1', 'Set NF_LIVE_ROAD_ATTRIBUTES=1 before launching Python; DLL CRT environment must inherit it'
class Identity(C.Structure):_fields_=[('epoch',C.c_uint64)]+[(k,C.c_uint32) for k in ('serial','begin','end','query','builder')]
Sink=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_uint64,C.c_void_p,C.c_size_t)
ids={}
@Sink
def sink(user,epoch,ptr,size):
    header=struct.unpack_from('<8I',C.string_at(ptr,32));serial,begin,end=header[4:7]
    ids[serial]=Identity(epoch,serial,begin,end,0,0)
    return 1
d=C.CDLL(str(p/'visibility-probe-wide.dll'))
d.nf_init.argtypes=[C.c_char_p,C.c_char_p];d.nf_state.argtypes=[C.c_char_p,C.c_int]
d.nf_native_scene_sink.argtypes=[Sink,C.c_void_p];d.nf_live_visibility_enable.argtypes=[C.c_void_p,C.c_size_t,C.c_size_t]
api=d.nf_live_completed_native_multimodel_world_classified_pair_packet
api.argtypes=[C.c_void_p,C.c_void_p,C.c_double,C.c_void_p,C.c_void_p,C.c_void_p]
d.nf_scene_packet_free.argtypes=[C.c_void_p]
assert d.nf_init(str(rom).encode(),b'') and d.nf_state(str(p.parent/'driving.state').encode(),0)
try:
    assert d.nf_native_scene_sink(sink,None)
    data=rom.read_bytes();assert d.nf_live_visibility_enable(data,len(data),16*1024*1024)
    d.nf_live_surface_audit_enable(1)
    for frame in range(800):
        d.nf_frame(1|(32 if 180<=frame<500 else 16 if 500<=frame<720 else 0))
        if 150 in ids:break
    assert all(i in ids for i in (148,149,150))
    assert ids[149].end==9451
    packets={};records=[]
    for name,a,b,alpha in [('left',148,149,1.),('right',149,150,0.),('left-near',148,149,1.-1e-8),('right-near',149,150,1e-8)]:
        out=C.c_void_p();size=C.c_size_t();stage=C.c_uint()
        assert api(C.byref(ids[a]),C.byref(ids[b]),alpha,C.byref(out),C.byref(size),C.byref(stage)),(name,stage.value)
        try:raw=C.string_at(out,size.value)
        finally:d.nf_scene_packet_free(out)
        packets[name]=raw;(p/f'shared-endpoint-{name}.packet').write_bytes(raw)
        records.append(dict(name=name,alpha=alpha,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()))
    assert packets['left']==packets['right'], 'Exact common source endpoint differs'
    class Section(C.Structure):_fields_=[('data',C.c_void_p),('size',C.c_size_t)]
    class Packet(C.Structure):_fields_=[('serial',C.c_uint),('begin',C.c_uint),('end',C.c_uint),('page',C.c_uint),('sections',Section*5)]
    d.nf_scene_packet_view.argtypes=[C.c_void_p,C.c_size_t,C.POINTER(Packet)]
    d.nf_live_completed_model_extract.argtypes=[C.c_uint64,C.c_uint32,C.c_uint32,C.c_uint32,C.c_void_p,C.c_void_p]
    d.nf_live_completed_surface_extract.argtypes=[C.c_uint64,C.c_uint32,C.c_uint32,C.c_uint32,C.c_uint32,C.c_void_p,C.c_void_p,C.c_void_p,C.c_void_p]
    d.nf_surface_free.argtypes=[C.c_void_p]
    def model_texture(data):
        magic,v,f,c,w,h=struct.unpack_from('<6I',data);assert magic==0x324d464e
        start=160+v*24+f+c*18
        return data[start:start+w*h*4]
    def world_texture(data,ring):
        pos=8
        for i in range(ring+1):
            n,w,h=struct.unpack_from('<3I',data,pos);start=pos+12+n*40;end=start+w*h*4
            if i==ring:return data[start:end]
            pos=end
    provenance=[]
    for serial,name in ((148,'left-near'),(149,'right-near')):
        identity=ids[serial];packet_owned=C.create_string_buffer(packets[name]);view=Packet()
        assert d.nf_scene_packet_view(packet_owned,len(packets[name]),C.byref(view))
        out=C.c_void_p();size=C.c_size_t()
        assert d.nf_live_completed_model_extract(identity.epoch,serial,identity.begin,identity.end,C.byref(out),C.byref(size))
        try:original_model=C.string_at(out,size.value)
        finally:d.nf_surface_free(out)
        generated_model=C.string_at(view.sections[0].data,view.sections[0].size)
        model_match=model_texture(original_model)==model_texture(generated_model)
        light=C.c_void_p();light_size=C.c_size_t()
        assert d.nf_live_completed_surface_extract(identity.epoch,serial,identity.begin,identity.end,30,C.byref(out),C.byref(size),C.byref(light),C.byref(light_size))
        try:surface=C.string_at(out,size.value)
        finally:d.nf_surface_free(out);d.nf_surface_free(light)
        n,w,h=struct.unpack_from('<3I',surface);original_texture=surface[12+n*40:12+n*40+w*h*4]
        generated_world=C.string_at(view.sections[1].data,view.sections[1].size)
        world_match=original_texture==world_texture(generated_world,30)
        assert model_match and world_match,(serial,model_match,world_match)
        provenance.append(dict(serial=serial,model_texture_matches_original_audited_capture=model_match,world_ring30_texture_matches_original_audited_capture=world_match))
    report=dict(result='PASS',shared_refresh=9451,simulated_refreshes=frame+1,exact_endpoint_packets_identical=True,records=records,texture_provenance=provenance,
                scope='Actual original simulation regenerates complete adjacent-pair packets at shared endpoint and near limits. Endpoint byte identity is not near-limit image continuity or smooth60fps proof.')
    (p/'shared-scene-endpoint-tests.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
finally:d.nf_close()
