"""Compare both traffic models to original completed draw geometry at endpoints."""
from pathlib import Path
import ctypes as C, struct, json, hashlib, math, csv, os
p=Path('work/camera').resolve()
rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba')
assert os.environ.get('NF_LIVE_ROAD_ATTRIBUTES')=='1', 'Set NF_LIVE_ROAD_ATTRIBUTES=1 before launching Python for production raw-road packets'
class Section(C.Structure): _fields_=[('data',C.c_void_p),('size',C.c_size_t)]
class Packet(C.Structure): _fields_=[(k,C.c_uint32) for k in ('serial','begin','end','page')]+[('sections',Section*5)]
Sink=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_uint64,C.c_void_p,C.c_size_t)
original={}; seen=[]
@Sink
def sink(user,epoch,ptr,size):
    raw=C.string_at(ptr,size); serial=struct.unpack_from('<I',raw,16)[0]
    seen.append(serial)
    if serial in (678,679,680,681): original[serial]=(epoch,raw)
    return 1
d=C.CDLL(str(p/'visibility-probe-wide.dll'))
d.nf_init.argtypes=[C.c_char_p,C.c_char_p];d.nf_state.argtypes=[C.c_char_p,C.c_int]
d.nf_native_scene_sink.argtypes=[Sink,C.c_void_p]
d.nf_live_visibility_enable.argtypes=[C.c_void_p,C.c_size_t,C.c_size_t]
d.nf_scene_packet_view.argtypes=[C.c_void_p,C.c_size_t,C.POINTER(Packet)]
d.nf_scene_packet_model_count.argtypes=[C.POINTER(Packet)]
d.nf_scene_packet_model.argtypes=[C.POINTER(Packet),C.c_uint, C.POINTER(Section)]
api=d.nf_live_completed_native_multimodel_owned
api.argtypes=[C.c_uint64,C.c_uint32,C.c_uint32,C.c_uint32,C.c_void_p,C.c_void_p,C.c_void_p]
class Identity(C.Structure):
    _fields_=[('epoch',C.c_uint64)]+[(k,C.c_uint32) for k in ('serial','begin','end','query','builder')]
pair=d.nf_live_completed_native_multimodel_world_classified_pair_packet
pair.argtypes=[C.c_void_p,C.c_void_p,C.c_double,C.c_void_p,C.c_void_p,C.c_void_p]
d.nf_scene_packet_free.argtypes=[C.c_void_p]
d.nf_pixels.restype=C.c_void_p
def models(raw):
    owned=C.create_string_buffer(raw);view=Packet()
    assert d.nf_scene_packet_view(owned,len(raw),C.byref(view))
    worlds=struct.unpack('<I',C.string_at(view.sections[1].data+4,4))[0]
    view.model_identities=[struct.unpack('<5I',C.string_at(view.sections[4].data+8+(worlds+i)*20,20)) for i in range(d.nf_scene_packet_model_count(C.byref(view)))]
    result=[]
    for i in range(d.nf_scene_packet_model_count(C.byref(view))):
        section=Section();assert d.nf_scene_packet_model(C.byref(view),i,C.byref(section))
        result.append(C.string_at(section.data,section.size))
    return view,result
assert d.nf_init(str(rom).encode(),b'') and d.nf_state(str(p.parent/'driving.state').encode(),0)
records=[]; endpoint_models={}; endpoint_ids={}; scene_ids={}; raster_refresh=None
try:
    assert d.nf_native_scene_sink(sink,None)
    assert d.nf_native_scene_multimodel(1)
    data=rom.read_bytes();assert d.nf_live_visibility_enable(data,len(data),16*1024*1024)
    d.nf_live_surface_audit_enable(1)
    for frame in range(3600):
        d.nf_frame(1|(32 if 180<=frame<500 else 16 if 500<=frame<720 else 0))
        if 678 in original and raster_refresh is None:
            from PIL import Image
            pixels=(C.c_uint32*(240*160)).from_address(d.nf_pixels())
            rgb=bytes(channel for pixel in pixels for channel in (pixel&255,(pixel>>8)&255,(pixel>>16)&255))
            Image.frombytes('RGB',(240,160),rgb).save(p/'traffic-original-678.png')
            raster_refresh=int(d.nf_native_scene_refresh())
        if 681 in original: break
    if len(original)!=4:
        report=dict(result='FAIL',reason='Target source scenes not retained',simulated_refreshes=frame+1,
                    callback_count=len(seen),last_serial=seen[-1] if seen else None,retained_serials=list(original))
        (p/'traffic-model-provenance-tests.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
    assert len(original)==4
    for serial,(epoch,raw) in sorted(original.items()):
        view,draws=models(raw);assert len(draws)==2
        endpoint_models[serial]=draws
        endpoint_ids[serial]=view.model_identities
        scene_ids[serial]=Identity(epoch,serial,view.begin,view.end,0,0)
        out=C.c_void_p();size=C.c_size_t();stage=C.c_uint()
        assert api(epoch,serial,view.begin,view.end,C.byref(out),C.byref(size),C.byref(stage)),stage.value
        try: _,regenerated=models(C.string_at(out,size.value))
        finally: d.nf_scene_packet_free(out)
        assert len(regenerated)==len(draws)
        for i,(a,b) in enumerate(zip(draws,regenerated)):
            # Header holds original rotation/camera/object; compare it too.
            magic,v,f,c,w,h=struct.unpack_from('<6I',a);assert magic==0x324d464e
            end=160+v*24+f+c*18
            same=a[:end]==b[:end]
            records.append(dict(serial=serial,model=i,vertices=v,geometry_bytes=end,
                                original_geometry_sha256=hashlib.sha256(a[:end]).hexdigest(),
                                regenerated_geometry_sha256=hashlib.sha256(b[:end]).hexdigest(),identical=same))
    def norm(q):
        length=math.sqrt(sum(x*x for x in q));return [x/length for x in q]
    def slerp(a,b,t):
        a=norm(a);b=norm(b);dot=sum(x*y for x,y in zip(a,b))
        if dot<0: b=[-x for x in b];dot=-dot
        if dot>.9995: return norm([(1-t)*x+t*y for x,y in zip(a,b)])
        angle=math.acos(min(1,dot));return norm([(math.sin((1-t)*angle)*x+math.sin(t*angle)*y)/math.sin(angle) for x,y in zip(a,b)])
    motion=[]
    sources=list(csv.DictReader((p/'traffic-source-sources.csv').open()))
    for index,source in enumerate(sources):
        older,newer=int(source['older']),int(source['newer'])
        sampled_view,sampled=models((p/f'traffic-{index:03}.packet').read_bytes())
        assert sampled_view.model_identities==endpoint_ids[older]==endpoint_ids[newer]
        t=float(source['alpha'])
        for i,model in enumerate(sampled):
            a=struct.unpack_from('<7d',endpoint_models[older][i],104)
            b=struct.unpack_from('<7d',endpoint_models[newer][i],104)
            actual=struct.unpack_from('<7d',model,104)
            expected_position=[(1-t)*x+t*y for x,y in zip(a[:3],b[:3])]
            expected_rotation=slerp(a[3:],b[3:],t);actual_rotation=norm(actual[3:])
            position_error=max(abs(x-y) for x,y in zip(expected_position,actual[:3]))
            quaternion_error=min(max(abs(x-y) for x,y in zip(expected_rotation,actual_rotation)),max(abs(x+y) for x,y in zip(expected_rotation,actual_rotation)))
            # Original object record quantizes positions to Q8 and rotations to Q14.
            assert position_error<=1/512+1e-8 and quaternion_error<.0002,(index,i,position_error,quaternion_error)
            def up_y(q):
                x,y,z,w=norm(q);return 1-2*(x*x+z*z)
            motion.append(dict(index=index,model=i,source_pair=[older,newer],identity=sampled_view.model_identities[i],alpha=t,position_error=position_error,quaternion_error=quaternion_error,
                               source_up_y=[up_y(a[3:]),up_y(b[3:])],sampled_up_y=up_y(actual[3:])))
    assert len(motion)==24
    def generate(a,b,t):
        out=C.c_void_p();size=C.c_size_t();stage=C.c_uint()
        assert pair(C.byref(scene_ids[a]),C.byref(scene_ids[b]),t,C.byref(out),C.byref(size),C.byref(stage)),stage.value
        try: return C.string_at(out,size.value)
        finally: d.nf_scene_packet_free(out)
    boundaries=[]
    for serial in (679,680):
        left=generate(serial-1,serial,1);right=generate(serial,serial+1,0)
        assert left==right
        boundaries.append(dict(serial=serial,refresh=scene_ids[serial].end,packet_bytes=len(left),sha256=hashlib.sha256(left).hexdigest(),identical=True))
    report=dict(result='PASS' if all(r['identical'] for r in records) else 'FAIL',simulated_refreshes=frame+1,records=records,motion=motion,
                boundaries=boundaries,original_raster_refresh=raster_refresh,original_raster_png_sha256=hashlib.sha256((p/'traffic-original-678.png').read_bytes()).hexdigest(),
                scope='Both models in four source scenes match original draw geometry; twelve moving displays across three pairs match independent interpolation within Q8/Q14 quantization with unchanged full model identities; production classified-world/raw-road exact pair-boundary packets identical. Does not prove original raster, visibility, normal driving, smooth60fps or physical gameplay fidelity.')
    (p/'traffic-model-provenance-tests.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
    assert report['result']=='PASS'
finally: d.nf_close()
