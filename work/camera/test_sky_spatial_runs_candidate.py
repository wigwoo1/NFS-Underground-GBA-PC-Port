import runpy,ctypes as C,json,math,struct
from pathlib import Path
ns=runpy.run_path('work/camera/test_sky_continuous_gpu_readback.py')
p=Path('work/camera');d=C.CDLL(str((p/'owned-sky-spatial-runs.dll').resolve()));api=d.nf_owned_gpu_render_sky;api.argtypes=ns['api'].argtypes
s=ns['samples'];a=C.create_string_buffer(s.lower);b=C.create_string_buffer(s.upper);checks=[]
# CPU reference uses destination-row palette, not RGB blending.
def color(i,index):
 c=struct.unpack_from('<H',ns['palettes'],((10560+i)//240)*512+index*2)[0]
 return tuple(((c>>k)&31)*8+(((c>>k)&31)>>2) for k in (0,5,10))
cell=max(range(240,14880),key=lambda i:max(abs(x-y) for x,y in zip(color(i,s.lower[i]),color(i,s.upper[i]))))
y,x=divmod(10560+cell,240);cols=[px for px in range(300,3540) if math.floor((px+.5-300)/13.5)==x]
try:
 for weight in (0,.2,.4,.6,.8,.99):
  assert api(ns['frame'],len(ns['raw']),a,b,15136,weight,ns['out'],len(ns['out']))==0
  pixels=ns['out'].raw;maximum=0
  for i in range(15136):
   yy,xx=divmod(10560+i,240);px=int(300+(xx+.5)*13.5);py=int((yy+.5)*13.5)
   frac=(px+.5-300)/13.5-xx
   expected=color(i,(s.upper if frac>=1-weight else s.lower)[i]);at=(py*3840+px)*3
   err=max(abs(v-w) for v,w in zip(pixels[at:at+3],expected));maximum=max(maximum,err);assert err<=1,(weight,i,err)
  py=int((y+.5)*13.5);upper=color(cell,s.upper[cell]);lower=color(cell,s.lower[cell]);upper_count=0
  for px in cols:
   at=(py*3840+px)*3;got=tuple(pixels[at:at+3]);assert got in (lower,upper)
   upper_count+=got==upper
  checks.append(dict(weight=weight,upper_columns=upper_count,cell_columns=len(cols),vertices=d.nf_sky_spatial_vertex_count(),max_channel_error=maximum))
 assert all(b['upper_columns']>a['upper_columns'] for a,b in zip(checks,checks[1:]))
finally:assert d.nf_owned_gpu_close()
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/sky-spatial-runs-candidate-20261007');cp.mkdir(exist_ok=True)
(cp/'result.json').write_text(json.dumps(dict(result='PASS',checks=checks,sky_centers_per_phase=15136,scope='Isolated 4K GPU nearest spatial-boundary candidate versus destination scanline palette CPU oracle. Not live performance, perceptual smoothness or full-scene fidelity proof.'),indent=2))
for name in ('test_sky_spatial_runs_candidate.py','generate_sky_spatial_candidate.py','owned_gpu_sky_spatial_diagnostic.c'):(cp/name).write_bytes((p/name).read_bytes())
print('PASS spatial sky GPU candidate',checks)
