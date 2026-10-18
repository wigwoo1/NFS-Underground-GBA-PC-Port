"""Measure spatial behavior of the current fractional sky GPU output."""
import runpy,ctypes as C,json,math
from pathlib import Path
ns=runpy.run_path('work/camera/test_source_sky_subpixel_gpu.py')
d=ns['d'];api=ns['api'];s=ns['sample'];setup=ns['ns'];assert d.nf_owned_gpu_window(0)==0
reference=setup['sky_rgba'](setup['SkySamples'](s.lower,s.upper,.5,s.destination),setup['palettes'])
# Select a visibly changing texel away from the partial final row.
lo=setup['sky_rgba'](setup['SkySamples'](s.lower,s.upper,0,s.destination),setup['palettes'])
index=max(range(240,14880),key=lambda i:max(abs(reference[i*4+k]-lo[i*4+k]) for k in range(3)))
y,x=divmod(10560+index,240);screen_y=int((y+.5)*13.5)
columns=[px for px in range(300,3540) if math.floor((px+.5-300)/13.5)==x]
checks=[]
try:
 for weight in (.2,.4,.6,.8):
  assert api(setup['frame'],len(setup['raw']),ns['a'],ns['b'],15136,weight,setup['out'],len(setup['out']))==0
  rgb=setup['out'].raw
  colors={tuple(rgb[(screen_y*3840+px)*3:(screen_y*3840+px)*3+3]) for px in columns}
  assert len(colors)==1,(weight,colors)
  checks.append(dict(weight=weight,color=list(next(iter(colors))),uniform_output_columns=len(columns)))
 assert len({tuple(c['color']) for c in checks})==4
finally:assert d.nf_owned_gpu_close()
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/source-sky-spatial-grid-20261007');cp.mkdir(exist_ok=True)
(cp/'result.json').write_text(json.dumps(dict(result='PASS_DIAGNOSTIC',source_cell=[x,y],screen_y=screen_y,columns=columns,checks=checks,finding='Fractional phases change color uniformly across a fixed enlarged source cell. This is fixed-grid crossfade, not continuously translated spatial edges.',scope='One high-contrast actual ROM sky cell in current-source 4K diagnostic GPU output; possible contributor to perceived stepping, not exclusive live cause or scanout evidence.'),indent=2))
(cp/Path(__file__).name).write_bytes(Path(__file__).read_bytes());print('PASS fixed-grid sky crossfade diagnostic',len(columns),'output columns')
