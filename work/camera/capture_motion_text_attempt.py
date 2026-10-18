import struct
"""Original source records for exact retained stable interval, preserved inputs."""
from pathlib import Path
import ctypes as C,csv,json,hashlib,os
from scene_batches import batches
p=Path('work/camera').resolve();source=p/'prototype-runs/racing-motion-audit-a88232ac136d4ad58dc7231b706de812';rows=list(csv.DictReader(Path(str(source)+'-input.csv').open()));rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba');state=p.parent/'race.state';dll=p/'visibility-probe-wide.dll';protected={str(x):hashlib.sha256(x.read_bytes()).hexdigest() for x in (rom,state,p.parent/'nfsprobe.dll')}
crt=C.CDLL('msvcrt');crt._putenv.argtypes=[C.c_char_p]
for k in list(os.environ):
 if k.startswith('NF_'):os.environ.pop(k,None);assert crt._putenv((k+'=').encode())==0
os.environ['NF_TEST_RACING_OWNED_CAPTURE']='1';assert crt._putenv(b'NF_TEST_RACING_OWNED_CAPTURE=1')==0
os.environ['NF_TRACE_ROAD_EDGE_ANIMATIONS']='1';assert crt._putenv(b'NF_TRACE_ROAD_EDGE_ANIMATIONS=1')==0
os.environ['NF_TRACE_MODEL_SPANS']='1';assert crt._putenv(b'NF_TRACE_MODEL_SPANS=1')==0
os.environ['NF_TRACE_DISPLAY_SNAPSHOTS']='1';assert crt._putenv(b'NF_TRACE_DISPLAY_SNAPSHOTS=1')==0
os.environ['NF_TRACE_DRAW_FRAMEBUFFER']='1';assert crt._putenv(b'NF_TRACE_DRAW_FRAMEBUFFER=1')==0
os.environ['NF_TRACE_INITIAL_WRITE_PCS']='1';assert crt._putenv(b'NF_TRACE_INITIAL_WRITE_PCS=1')==0
os.environ['NF_TRACE_SPRITE_SNAPSHOTS']='1';assert crt._putenv(b'NF_TRACE_SPRITE_SNAPSHOTS=1')==0
os.environ['NF_TRACE_SPRITE_WRITES']='1';assert crt._putenv(b'NF_TRACE_SPRITE_WRITES=1')==0
trace=p/'motion-original-scanline-state-world.bin';d=C.CDLL(str(dll));d.nf_capture.argtypes=[C.c_char_p];d.nf_init.argtypes=[C.c_char_p]*2;d.nf_state.argtypes=[C.c_char_p,C.c_int];d.nf_world_trace.argtypes=[C.c_char_p];d.nf_dump.argtypes=[C.c_char_p,C.c_uint,C.c_uint];d.nf_native_scene_refresh.restype=C.c_uint
d.nf_pixels.restype=C.c_void_p
d.nf_bitmap_text_enable.argtypes=[C.c_uint]
d.nf_bitmap_blit_trace.argtypes=[C.c_char_p]
Sink=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_uint64,C.c_void_p,C.c_size_t)
@Sink
def text_scene_sink(context,epoch,data,size):return 1
d.nf_native_scene_sink.argtypes=[Sink,C.c_void_p]
d.nf_live_visibility_enable.argtypes=[C.c_void_p,C.c_size_t,C.c_size_t]
d.nf_layer_queue_text_row.argtypes=[C.c_uint64,C.c_uint,C.c_uint,C.c_void_p,C.c_void_p,C.c_uint]
d.nf_layer_capture_row.argtypes=[C.c_uint,C.c_void_p,C.c_uint]
targets=[8758,8762,8766,8769,8773,8776,8780];captured=[];pending=None
d.nf_native_scene_epoch.restype=C.c_uint64
d.nf_layer_queue_native_rgb4.argtypes=[C.c_uint64,C.c_uint,C.c_void_p,C.c_uint,C.c_void_p,C.c_uint]
d.nf_geometry_sources_read.argtypes=[C.c_uint,C.c_void_p,C.c_size_t,C.c_void_p]
d.nf_native_live_background_coverage.argtypes=[C.c_uint,C.c_void_p,C.c_uint]
d.nf_native_live_background_vram.argtypes=[C.c_uint,C.c_void_p,C.c_uint]
d.nf_native_live_frame_vram.argtypes=[C.c_uint,C.c_void_p,C.c_uint,C.c_void_p]
d.nf_native_model_plan_trace.argtypes=[C.c_char_p,C.c_void_p,C.c_uint]
model_plan_table=(p/'road-correction-reciprocal.bin').read_bytes()
queue_checks=[]
scan_assets=p/'motion-actual-scanline-assets';scan_assets.mkdir(exist_ok=True)
rgb_assets=p/'motion-actual-rgb-assets';rgb_assets.mkdir(exist_ok=True)
assert d.nf_init(str(rom).encode(),b'') and d.nf_state(str(state).encode(),0);assert d.nf_native_scene_sink(text_scene_sink,None);rom_owned=rom.read_bytes();assert d.nf_live_visibility_enable(rom_owned,len(rom_owned),16*1024*1024);assert d.nf_bitmap_text_enable(1);started=False;ended=False
try:
 for row in rows:
  before=d.nf_native_scene_refresh()
  if before>=8749 and not started:assert d.nf_bitmap_blit_trace(str(p/'motion-text-glyph-audit.csv').encode());assert d.nf_world_trace(str(trace).encode());d.nf_capture(str(p/'motion-original-scanline-state-hooks.bin').encode());started=True;assert d.nf_layer_queue_enable(1);assert d.nf_native_model_plan_trace(str(p/'motion-live-native-model-plans.bin').encode(),model_plan_table,len(model_plan_table))
  if pending is None and len(captured)<len(targets) and before>=targets[len(captured)]:
   assert before==targets[len(captured)],(before,targets[len(captured)]);assert d.nf_layer_capture_arm();pending=before
  d.nf_frame(int(row['keys']))
  if pending is not None and d.nf_layer_capture_status()==3:
   size=d.nf_layer_row_size();out=C.create_string_buffer(size);data=bytearray()
   for y in range(160):assert d.nf_layer_capture_row(y,out,size);data.extend(out.raw)
   assert int.from_bytes(data[:4],'little')==pending
   (scan_assets/f'{pending}-rows.bin').write_bytes(data);(scan_assets/f'{pending}-rgb.bin').write_bytes(C.string_at(d.nf_pixels(),240*160*4));captured.append(pending);pending=None
   geometry_size=C.c_size_t();assert d.nf_geometry_sources_read(captured[-1],None,0,C.byref(geometry_size))
   geometry=C.create_string_buffer(geometry_size.value);assert d.nf_geometry_sources_read(captured[-1],geometry,len(geometry),C.byref(geometry_size))
   assert geometry_size.value>0;(scan_assets/f'{captured[-1]}-model-sources.bin').write_bytes(geometry.raw)
   hud_bytes=b''.join(data[y*100480:y*100480+128]+data[y*100480+128+0x10000:y*100480+128+0x18000]+data[y*100480+98432:(y+1)*100480] for y in range(160))
   (scan_assets/f'{captured[-1]}-hud-owned.bin').write_bytes(hud_bytes)
   text=bytearray();text_mask=bytearray()
   for y in range(160):
    ti=C.create_string_buffer(240);tm=C.create_string_buffer(240);assert d.nf_layer_queue_text_row(d.nf_native_scene_epoch(),captured[-1],y,ti,tm,240)
    text.extend(ti.raw);text_mask.extend(tm.raw)
   (scan_assets/f'{captured[-1]}-text-owned.bin').write_bytes(text+text_mask)
   print(dict(text_refresh=captured[-1],covered_text_pixels=sum(text_mask)))
   frame_header=struct.pack('<4I',0x3146474e,captured[-1],len(geometry.raw),len(hud_bytes))
   (scan_assets/f'{captured[-1]}-owned-frame.bin').write_bytes(frame_header+geometry.raw+hud_bytes)
   background=C.create_string_buffer(0x18000);assert d.nf_native_live_background_vram(captured[-1],background,len(background))
   (scan_assets/f'{captured[-1]}-native-background.bin').write_bytes(background.raw)
   coverage=C.create_string_buffer(0x18000);assert d.nf_native_live_background_coverage(captured[-1],coverage,len(coverage))
   (scan_assets/f'{captured[-1]}-native-background-coverage.bin').write_bytes(coverage.raw)
   page=0xa000 if struct.unpack_from('<H',hud_bytes,8)[0]&16 else 0
   image=bytes(background.raw[page+i] if coverage.raw[page+i] else 0 for i in range(38400));mask=coverage.raw[page:page+38400]
   (scan_assets/f'{captured[-1]}-owned-background-frame.bin').write_bytes(struct.pack('<5I',0x3246474e,captured[-1],len(geometry.raw),len(hud_bytes),76800)+geometry.raw+hud_bytes+image+mask)
   captured_refresh=captured[-1];closing={8758:8757,8762:8761,8766:8765,8769:8768,8773:8772,8776:8775,8780:8779}[captured_refresh]
   vram=C.create_string_buffer(0x18000);generation=C.c_uint64();assert d.nf_native_live_frame_vram(captured_refresh,vram,0x18000,C.byref(generation));rgb=(C.c_uint32*38400)();epoch=d.nf_native_scene_epoch()
   assert d.nf_layer_queue_native_rgb4(epoch,captured_refresh,vram,len(vram),rgb,C.sizeof(rgb))
   expected=C.string_at(d.nf_pixels(),240*160*4);expected=b''.join((int.from_bytes(expected[i:i+4],'little')&0xffffff).to_bytes(4,'little') for i in range(0,len(expected),4));assert bytes(rgb)==expected
   sentinel=bytes(rgb);assert not d.nf_layer_queue_native_rgb4(epoch+1,captured_refresh,vram,len(vram),rgb,C.sizeof(rgb));assert bytes(rgb)==sentinel
   queue_checks.append(dict(refresh=captured_refresh,pixels=38400,stale_epoch_rejected=True,live_native_generation=generation.value))
   print(dict(captured_rows=160,row_bytes=size,header_refresh=int.from_bytes(data[:4],'little'),completed_refresh=d.nf_native_scene_refresh()))
  refresh=d.nf_native_scene_refresh()
  if 8750<=refresh<=8781:(rgb_assets/f'{refresh}-rgb.bin').write_bytes(C.string_at(d.nf_pixels(),240*160*4))
  if started and not ended and d.nf_native_scene_refresh()>=8781:d.nf_native_model_plan_trace(None,None,0);d.nf_world_trace(None);d.nf_capture(None);ended=True
 assert started and ended and captured==targets
 for name,base,size in [('ewram',0x02000000,0x40000),('iwram',0x03000000,0x8000)]:
  target=p/f'motion-original-scanline-state-{name}.bin';d.nf_dump(str(target).encode(),base,size);assert target.read_bytes()==Path(str(source)+'-'+name+'.bin').read_bytes(),name
finally:d.nf_bitmap_blit_trace(None);d.nf_native_model_plan_trace(None,None,0);d.nf_capture(None);d.nf_world_trace(None);d.nf_close()
selected=[b for b in batches(trace) if b['begin_refresh']>=8750 and b['end_refresh']<=8781];assert len(selected)>=2
scenes=[]
for batch in selected:
 roads=[e for e in batch['events'] if e['pc']==0x030032f0]
 scenes.append(dict(begin=batch['begin_refresh'],end=batch['end_refresh'],page=batch['display_page'],roads=[dict(event=e['id'],refresh=e['frame'],source=e['blocks'][4][0],blocks={str(k):dict(address=a,hex=data.hex()) for k,(a,data) in e['blocks'].items()}) for e in roads]))
(p/'live-queue-native-rgb-tests.json').write_text(json.dumps(dict(result='PASS_LIVE_QUEUE_NATIVE_RGB',checks=queue_checks,pixels=sum(x['pixels'] for x in queue_checks),scope='Live original-input replay composes historical scanline queue state from live retained native scene VRAM snapshots; no prerecorded native VRAM assets used. No GPU4K or timing claim.'),indent=2),encoding='utf-8')
report=dict(result='ORIGINAL_MOTION_INTERVALS_CAPTURED',scenes=scenes,trace_sha256=hashlib.sha256(trace.read_bytes()).hexdigest(),original_final_ram_exact=True,scope='Read-only original road source records and matrix blocks across consecutive completed game scenes replayed from unchanged race state/input ledger. Current interpolated world pose not inferred from screen polygons; raw prepared streams are oracle only.')
assert all(hashlib.sha256(Path(x).read_bytes()).hexdigest()==v for x,v in protected.items());(p/'motion-original-scanline-state-capture.json').write_text(json.dumps(report,indent=2));print(dict(result=report['result'],scenes=len(scenes),roads=sum(len(s['roads']) for s in scenes),trace_bytes=trace.stat().st_size,original_final_ram_exact=True))
