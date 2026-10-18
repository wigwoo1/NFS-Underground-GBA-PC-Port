"""Read-only original per-refresh motion/display measurements during selection."""
import ctypes as C,struct,json,hashlib,uuid
from pathlib import Path
crt=C.CDLL('msvcrt');crt._putenv_s.argtypes=[C.c_char_p,C.c_char_p];assert crt._putenv_s(b'NF_CAPTURE_MODEL_VIEWS',b'1')==0
p=Path(__file__).resolve().parent;P=C.c_void_p;U=C.c_uint32;Z=C.c_size_t
rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba');state=p/'prototype-runs/menu-navigation/quick-1-release.state'
d=C.CDLL(str(p/'visibility-probe-wide.dll'));d.nf_init.argtypes=[C.c_char_p]*2;d.nf_state.argtypes=[C.c_char_p,C.c_int];d.nf_pixels.restype=P;d.nf_read.argtypes=[U,C.c_int];d.nf_read.restype=U;d.nf_live_visibility_enable.argtypes=[P,Z,Z];d.nf_dump.argtypes=[C.c_char_p,U,U]
Sink=C.CFUNCTYPE(C.c_int,P,C.c_uint64,P,Z);d.nf_native_scene_sink.argtypes=[Sink,P]
d.nf_live_completed_draw_timing.argtypes=[C.c_uint64,U,U,P]
d.nf_layer_queue_selection_page_equal.argtypes=[C.c_uint64,U,U]
d.nf_layer_queue_selection_scene_hold.argtypes=[C.c_uint64,U,U,U]
publications=[];latest={};rows=[];display_frames={}
@Sink
def sink(ctx,epoch,data,size):
 raw=C.string_at(data,size);serial,begin,end,page=struct.unpack_from('<4I',raw,16);wo=struct.unpack_from('<I',raw,48)[0];world_count=struct.unpack_from('<I',raw,wo+4)[0];io=struct.unpack_from('<I',raw,84)[0];identity=struct.unpack_from('<5I',raw,io+8+world_count*20)
 latest.update(page=page,epoch=epoch,end=end,serial=serial,state=identity[1],object=identity[2]);views=[]
 for ordinal in range(4):
  timing=(U*6)()
  if not d.nf_live_completed_draw_timing(epoch,serial,ordinal,timing):break
  views.append(dict(ordinal=ordinal,root_refresh=timing[0],model_draw_refresh=timing[1],root_display_control=timing[2],model_display_control=timing[3],framebuffer_base=timing[4],world_draws_before_model=timing[5]))
 publications.append(dict(serial=serial,begin=begin,end=end,views=views));return 1
def words(address,count):return [d.nf_read(address+i*4,4) for i in range(count)]
assert d.nf_init(str(rom).encode(),b'') and d.nf_state(str(state).encode(),0)
assert d.nf_native_scene_sink(sink,None) and d.nf_native_scene_multimodel(1);raw=rom.read_bytes();assert d.nf_live_visibility_enable(raw,len(raw),16*1024*1024);d.nf_live_surface_audit_enable(1);assert d.nf_layer_queue_enable(1)
d.nf_bitmap_dma_trace.argtypes=[C.c_char_p]
run=p/'prototype-runs'/('selection-motion-'+uuid.uuid4().hex);actual=[]
assert d.nf_bitmap_dma_trace(str(Path(str(run)+"-dma-writes.csv")).encode())
try:
 for step in range(240):
  keys=16 if 90<=step<92 or 180<=step<182 else 0;d.nf_frame(keys);row=dict(step=step,keys=keys,refresh=d.nf_layer_queue_latest(),latest_serial=latest.get('serial'),display_control=d.nf_read(0x04000000,2),mode=d.nf_read(0x03005f14,4),frontend=d.nf_read(0x03006710,1),display_sha256=hashlib.sha256(C.string_at(d.nf_pixels(),240*160*4)).hexdigest())
  if latest:
   row['display_page_equal_latest']=bool(d.nf_layer_queue_selection_scene_hold(latest['epoch'],latest['end'],latest['page'],row['refresh']))
   camera=d.nf_read(latest['state']+84,4);row.update(camera_words=words(camera,12),object_position_words=words(latest['object']+12,3),model_pointer=d.nf_read(latest['object']+140,4))
   row['object_rotation_words']=words(row['model_pointer']+320,9)
  if row['refresh'] in [3524,3525,3543,3544,3615,3616,3633,3634]:display_frames[row['refresh']]=C.string_at(d.nf_pixels(),240*160*4)
  rows.append(row)
 for name,base,n in [('ewram',0x02000000,0x40000),('iwram',0x03000000,0x8000)]:
  path=Path(str(run)+'-'+name+'.bin');d.nf_dump(str(path).encode(),base,n);actual.append(path.read_bytes())
finally:d.nf_close()
b=C.CDLL(str(p.parent/'nfsprobe.dll'));b.nf_init.argtypes=[C.c_char_p]*2;b.nf_state.argtypes=[C.c_char_p,C.c_int];b.nf_dump.argtypes=[C.c_char_p,U,U];assert b.nf_init(str(rom).encode(),b'') and b.nf_state(str(state).encode(),0)
try:
 for row in rows:b.nf_frame(row['keys'])
 for expected,(name,base,n) in zip(actual,[('ewram',0x02000000,0x40000),('iwram',0x03000000,0x8000)]):
  path=Path(str(run)+'-baseline-'+name+'.bin');b.nf_dump(str(path).encode(),base,n);assert path.read_bytes()==expected
finally:b.nf_close()
gaps=[]
for a,z in zip(publications,publications[1:]):
 if z['end']-a['end']>8:
  inside=[r for r in rows if a['end']<=r['refresh']<z['end']]
  gaps.append(dict(older=a,newer=z,measured_refreshes=len(inside),unique_display_hashes=len({r['display_sha256'] for r in inside}),unique_camera_states=len({tuple(r['camera_words']) for r in inside}),unique_object_positions=len({tuple(r['object_position_words']) for r in inside}),display_page_equal_refreshes=[r['refresh'] for r in inside if r.get('display_page_equal_latest')],latest_serials=sorted({r['latest_serial'] for r in inside}),unique_object_rotations=len({tuple(r['object_rotation_words']) for r in inside}),display_change_refreshes=[r['refresh'] for prior,r in zip(inside,inside[1:]) if r['display_sha256']!=prior['display_sha256']],camera_change_refreshes=[r['refresh'] for prior,r in zip(inside,inside[1:]) if r['camera_words']!=prior['camera_words']],display_controls=sorted({r['display_control'] for r in inside})))
display_differences=[]
from PIL import Image
for a,z in [(3524,3525),(3543,3544),(3615,3616),(3633,3634)]:
 left,right=display_frames[a],display_frames[z];changes=[i for i in range(240*160) if left[i*4:i*4+4]!=right[i*4:i*4+4]];by_row=[sum(i//240==y for i in changes) for y in range(160)]
 display_differences.append(dict(older_refresh=a,newer_refresh=z,changed_pixels=len(changes),bounds=None if not changes else [min(i%240 for i in changes),min(i//240 for i in changes),max(i%240 for i in changes)+1,max(i//240 for i in changes)+1],changed_rows={y:n for y,n in enumerate(by_row) if n}))
 for refresh in [a,z]:Image.frombytes('RGBA',(240,160),display_frames[refresh]).save(Path(str(run)+'-display-'+str(refresh)+'.png'))
report=dict(result='PASS',display_differences=display_differences,original_updates=len(rows),exact_final_original_ram=True,publication_gaps=gaps,scope='Original per-refresh camera/object memory and complete emulator display hashes; no polygon matching or native pixel parity/smooth60fps proof.')
Path(str(run)+'-rows.json').write_text(json.dumps(rows,indent=2));Path(str(run)+'-report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2));print(run)
