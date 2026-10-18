"""Duplicate sealed palettes must not repeat scene-owned asset extraction."""
from pathlib import Path
import ctypes as C,json,runpy,sys
p=Path('work/camera');sys.path.insert(0,str(p.resolve()));sys.argv=['oracle','0.5','motion','road-full']
ns=runpy.run_path(str(p/'test_sampled_object_dispatch.py'));d=ns['d'];P=C.c_void_p;U=C.c_uint;Read=ns['Read']
d.nf_draw_palettes_create.argtypes=[C.c_uint64,U];d.nf_draw_palettes_create.restype=P
d.nf_draw_palettes_append.argtypes=[P,U,U,U,P,C.c_size_t];d.nf_draw_palettes_seal.argtypes=[P];d.nf_draw_palettes_destroy.argtypes=[P]
fn=d.nf_scene_command_palette;fn.argtypes=[P,C.c_uint64,U,P,Read,P,P,P]
stats=d.nf_scene_command_palette_stats;stats.argtypes=[P];before=(C.c_uint64*6)();stats(before)
counts=[];epoch=43;serial=17;palette=ns['model_inputs'][48:]
for copies in (1,64):
 command=next(c for c in ns['commands'] if c.kind==1);bank=d.nf_draw_palettes_create(epoch,serial);assert bank
 try:
  for _ in range(copies):assert d.nf_draw_palettes_append(bank,1,command.source,command.material[1],palette,512)
  assert d.nf_draw_palettes_seal(bank)
  reads=[]
  @Read
  def reader(ctx,address,out,size):
   reads.append((address,size));return ns['immutable_reader'](ctx,address,out,size)
  out=C.create_string_buffer(b'X'*512,512)
  assert fn(bank,epoch,serial,C.byref(command),reader,None,ns['model_inputs'][:48],out) and out.raw==palette
  counts.append(list(reads));assert reads
  out.raw=b'X'*512;assert not fn(bank,epoch+1,serial,C.byref(command),reader,None,ns['model_inputs'][:48],out) and out.raw==b'X'*512
 finally:d.nf_draw_palettes_destroy(bank)
assert counts[0]==counts[1]
after=(C.c_uint64*6)();stats(after);assert after[2]-before[2]==63
# A different visible palette must still be extracted and rejected.
bank=d.nf_draw_palettes_create(epoch,serial)
try:
 altered=bytes(v^255 for v in palette)
 for colors in (palette,altered):assert d.nf_draw_palettes_append(bank,1,command.source,command.material[1],colors,512)
 assert d.nf_draw_palettes_seal(bank);out=C.create_string_buffer(b'X'*512,512)
 assert not fn(bank,epoch,serial,C.byref(command),ns['immutable_reader'],None,ns['model_inputs'][:48],out) and out.raw==b'X'*512
finally:d.nf_draw_palettes_destroy(bank)
report=dict(result='PASS',duplicate_palettes=64,asset_reads_single=len(counts[0]),asset_reads_duplicate=len(counts[1]),atomic_epoch_rejections=2,visible_palette_difference_rejected=True,scope='One owned captured road command and sealed bank; duplicate bytes avoid repeated extraction while differing palette still validates. No performance or full-scene fidelity claim.')
(p/'command-palette-duplicate-tests.json').write_text(json.dumps(report,indent=2));print(report)
