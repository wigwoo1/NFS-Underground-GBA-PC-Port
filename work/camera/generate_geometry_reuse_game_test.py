from pathlib import Path
p=Path('work/camera');s=(p/'test_capture_cycles_snapshot_parity.py').read_text()
s=s.replace('capture-cycles-20261007','geometry-reuse-20261008').replace("'viewport-sky-cycles-probe.dll'","'viewport-sky-geometry-reuse-probe.dll'")
s=s.replace('pixels=[];cycles=[];layers=[];graphs=[]','pixels=[];cycles=[];layers=[];graphs=[];frames=[]')
s=s.replace('d.nf_native_scene_epoch.restype=C.c_uint64','d.nf_native_scene_epoch.restype=C.c_uint64\n d.nf_native_owned_frame_read.argtypes=[C.c_uint64,C.c_uint,C.c_void_p,C.c_size_t,C.POINTER(C.c_size_t)]')
needle="   if 'cycles' in name:"
insert='''   latest=d.nf_native_live_latest_frame()
   if latest and (not frames or frames[-1]['refresh']!=latest):
    n=C.c_size_t();assert d.nf_native_owned_frame_read(epoch,latest,None,0,C.byref(n))
    packet=C.create_string_buffer(n.value);assert d.nf_native_owned_frame_read(epoch,latest,packet,n.value,C.byref(n))
    frames.append(dict(refresh=latest,bytes=n.value,sha256=hashlib.sha256(packet.raw).hexdigest()))
    sentinel=C.create_string_buffer(b'unchanged',9);bad=C.c_size_t()
    assert not d.nf_native_owned_frame_read(epoch,latest,sentinel,9,C.byref(bad)) and sentinel.raw==b'unchanged'
    assert not d.nf_native_owned_frame_read(epoch+1,latest,sentinel,9,C.byref(bad)) and sentinel.raw==b'unchanged'
'''
assert s.count(needle)==1;s=s.replace(needle,insert+needle)
s=s.replace('cycles=cycles,layers=layers,graphs=graphs','cycles=cycles,layers=layers,graphs=graphs,complete_frames=frames')
s=s.replace("assert runs[0]['layers']==","assert runs[0]['complete_frames']==runs[1]['complete_frames'] and runs[0]['complete_frames']\nassert runs[0]['layers']==")
s=s.replace('snapshot-parity.json','complete-game-parity.json').replace('does not prove every scene/sky transport or live performance','complete captured frames exact with undersized/wrong-epoch atomic rejection; route diagnostic, not fullgame coverage or live pacing')
(p/'test_geometry_reuse_game_parity.py').write_text(s)
