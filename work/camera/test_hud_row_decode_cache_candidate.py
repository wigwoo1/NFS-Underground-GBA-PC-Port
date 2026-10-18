import sys,json,ctypes as C,struct
from pathlib import Path
sys.argv=['fixture','work/camera/prototype-runs/owned-native-1791434872973979000.json']
exec(compile(Path('work/camera/test_owned_native_source_backdrop_batch_parity_candidate.py').read_text().split('session=None;results=[]')[0],'saved-scene','exec'))
d=C.CDLL(str(Path('work/camera/owned-hud-row-decode-cache-candidate.dll').resolve()));d.nf_hud_row_decode_cached.argtypes=[C.c_uint64,C.c_void_p,C.c_void_p];d.nf_hud_row_decode_direct.argtypes=[C.c_void_p,C.c_void_p]
size=34944;output_size=240*10;checks=0
try:
 for frame in (frames[0],frames[0],frames[1],frames[1]):
  h=struct.unpack_from('<6I2Q',frame);assert h[3]==160*size
  for y in range(160):
   raw=frame[40+h[2]+y*size:40+h[2]+(y+1)*size];row=C.create_string_buffer(raw);a=C.create_string_buffer(output_size);b=C.create_string_buffer(output_size)
   assert d.nf_hud_row_decode_direct(row,a)==1;assert d.nf_hud_row_decode_cached(h[6],row,b)==1;assert a.raw==b.raw;checks+=1
 stats=(C.c_uint64*3)();assert d.nf_hud_row_cache_stats(stats)==1;assert stats[0]>0 and stats[1]>0 and stats[2]<6*1024*1024
 # A new epoch must miss even with exact same decoder inputs.
 observed_hits,observed_misses=int(stats[0]),int(stats[1]);before=stats[1];assert d.nf_hud_row_decode_cached(h[6]+1,row,b)==1;assert d.nf_hud_row_cache_stats(stats)==1 and stats[1]==before+1
 bad=bytearray(raw);struct.pack_into('<I',bad,4,160);assert d.nf_hud_row_decode_cached(h[6]+1,C.create_string_buffer(bytes(bad)),b)==0
 d.nf_hud_row_cache_clear();assert d.nf_hud_row_cache_stats(stats)==1 and stats[0]==stats[1]==0
 out=dict(result='PASS_EXACT_SAVED_HUD_ROW_DECODE_CACHE',scanlines=checks,hits=observed_hits,misses=observed_misses,cache_bytes=stats[2],scope='Exact native colors/tags/window/backdrop controls for two saved HUD frames repeated; epoch reset and invalid row rejection. Standalone decoder component only, no live renderer or full4K parity proof.')
 Path('work/camera/prototype-runs/hud-row-decode-cache-20261009.json').write_text(json.dumps(out,indent=2));print(out)
finally:history.close()
