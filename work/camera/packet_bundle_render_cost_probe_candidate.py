"""Matched full render calls on the same actual published source packet."""
import ast,textwrap,time,statistics
from pathlib import Path
from owned_uncovered_window_candidate import OwnedD3DConsumer
from owned_renderer_fixed_types_install_candidate import U32_3,U32_2,F32_4
bundled=OwnedD3DConsumer.render;results=[]
source=Path(__file__).with_name('owned_source_d3d_sky_pan_candidate.py').read_text();tree=ast.parse(source);cls=next(x for x in tree.body if isinstance(x,ast.ClassDef));method=next(x for x in cls.body if isinstance(x,ast.FunctionDef) and x.name=='render');source=textwrap.dedent(ast.get_source_segment(source,method))
for old,new in [('(C.c_uint*3)()','U32_3()'),('(C.c_uint*2)()','U32_2()'),('(C.c_float*4)(.035,.05,.08,1)','F32_4(.035,.05,.08,1)')]:source=source.replace(old,new)
ns=dict(bundled.__globals__);ns.update(U32_3=U32_3,U32_2=U32_2,F32_4=F32_4);exec(compile(source,'matched-original-render','exec'),ns);baseline=ns['render']
def render(self,s,readback=True):
 if not results:
  trials=[]
  for repetition in range(8):
   modes=[('baseline',baseline),('bundle',bundled)]
   if repetition%2:modes.reverse()
   for name,fn in modes:
    for _ in range(10):fn(self,s,False)
    begin=time.perf_counter_ns()
    for _ in range(30):fn(self,s,False)
    trials.append(dict(mode=name,ns_per_render=(time.perf_counter_ns()-begin)/30))
  medians={mode:statistics.median(x['ns_per_render'] for x in trials if x['mode']==mode) for mode in ('baseline','bundle')}
  results.append(dict(median_ns=medians,trials=trials,scope='Alternating warm complete consumer renders of one actual published source packet, including float conversion and D3D upload/draw submissions. No source regeneration/Present or physical GPU completion timing, no live cadence claim.'))
 return bundled(self,s,readback)
OwnedD3DConsumer.render=render
