import ctypes as C,os,json,time,struct
from pathlib import Path
cache=Path(os.environ['TEMP'])/'NFSUG-Native-Geometry-Preview-20261014'
os.environ['NF_LAYER_DIRTY']='1';os.environ['NF_TEST_RACING_OWNED_CAPTURE']='1'
# The bridge imports msvcrt; synchronize its CRT environment, not only Python's.
crt=C.CDLL('msvcrt.dll');crt._putenv.argtypes=[C.c_char_p]
for entry in (b'NF_LAYER_DIRTY=1',b'NF_TEST_RACING_OWNED_CAPTURE=1'):assert crt._putenv(entry)==0
with os.add_dll_directory(str(cache)):
 d=C.CDLL(str(cache/'nfsprobe.dll'))
 d.nf_init.argtypes=[C.c_char_p,C.c_char_p];d.nf_state.argtypes=[C.c_char_p,C.c_int]
 d.nf_native_scene_epoch.restype=C.c_uint64;d.nf_native_scene_refresh.restype=C.c_uint
 d.nf_layer_queue_hud_row.argtypes=[C.c_uint64,C.c_uint,C.c_uint,C.c_void_p,C.c_uint]
 d.nf_layer_queue_text_row.argtypes=[C.c_uint64,C.c_uint,C.c_uint,C.c_void_p,C.c_void_p,C.c_uint]
 assert d.nf_init(os.fsencode(cache/'game.gba'),b'')
 try:
  d.nf_60(0);assert d.nf_state(os.fsencode(cache/'checkpoint.state'),0)
  Sink=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_uint64,C.c_void_p,C.c_size_t)
  sink=Sink(lambda context,epoch,data,size:1)
  d.nf_native_scene_sink.argtypes=[Sink,C.c_void_p]
  assert d.nf_native_scene_sink(sink,None);assert d.nf_native_scene_multimodel(1)
  assert d.nf_layer_queue_enable(1);assert d.nf_bitmap_text_enable(1)
  begin=time.perf_counter()
  for i in range(80):d.nf_frame(1)
  elapsed=time.perf_counter()-begin;epoch=d.nf_native_scene_epoch();refresh=d.nf_layer_queue_latest()
  size=d.nf_layer_hud_row_size();rows=C.create_string_buffer(size*160);indices=C.create_string_buffer(240);coverage=C.create_string_buffer(240)
  d.nf_layer_queue_context.argtypes=[C.c_uint64,C.c_uint,C.c_void_p]
  context=(C.c_uint*3)();print('epoch/refresh/context',epoch,refresh,d.nf_layer_queue_context(epoch,refresh,context),list(context))
  checks=[];text_rows=0
  for y in range(160):
   assert d.nf_layer_queue_hud_row(epoch,refresh,y,C.byref(rows,y*size),size)
   text_rows+=bool(d.nf_layer_queue_text_row(epoch,refresh,y,indices,coverage,240))
  assert text_rows==160, "Text capture unavailable; check the bridge CRT environment"
  assert not d.nf_layer_queue_hud_row(epoch+1,refresh,0,rows,size)
  assert not d.nf_layer_queue_hud_row(epoch,refresh,160,rows,size)
  result=dict(epoch=epoch,refresh=refresh,row_bytes=size,rows=160,text_rows=text_rows,context=list(context),first_affine=struct.unpack_from("<6i",rows.raw,104),display=struct.unpack_from("<H",rows.raw,8)[0],frames=80,unpaced_seconds=elapsed)
  Path(r'C:\NFSUG-Workspace\NFSUG-packet-live-local\bounded-build\hud-input-probe.json').write_text(json.dumps(result,indent=2))
  print(json.dumps(result));print('PASS: 160 matching HUD rows; captured text rows:',text_rows)
 finally:d.nf_close()