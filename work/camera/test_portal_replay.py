"""Sampled candidate replay containment and exact endpoint regression."""
from pathlib import Path
import os,json,subprocess,math
from PIL import Image,ImageChops
p=Path('work/camera').resolve()
samples=json.loads((p/'texture-provenance-tests.json').read_text())['portal_samples']
def render(exe,older,alpha,label,bounds=None):
 env=os.environ.copy();env['NF_PREVIEW_FRACTION']=str(alpha);env['NF_PREVIEW_PHASE']='2';env.pop('NF_CANDIDATE_PORTAL',None)
 if bounds is not None:env['NF_CANDIDATE_PORTAL']=','.join(map(str,bounds))
 prefix=p/label
 subprocess.run([str(p/exe),str(p/older),str(p/'order-boundary-141.bin'),str(prefix)],env=env,check=True,capture_output=True)
 with Image.open(str(prefix)+'-2.ppm') as image:return image.copy()
def count_changed(diff):
 r,g,b=diff.split();mask=ImageChops.lighter(ImageChops.lighter(r,g),b);return diff.width*diff.height-mask.histogram()[0]
rows=[];previous=None;previous_control=None
for i,s in enumerate(samples):
 plans=s['draw_plans'];bounds=plans[0]['viewport'] if plans else None
 a=render('portal-candidate-preview.exe','candidate-140.bin',s['alpha'],f'portal-phase-{i}',bounds)
 b=render('packet-depth-preview.exe','order-boundary-140.bin',s['alpha'],f'portal-control-{i}')
 diff=ImageChops.difference(a,b);box=diff.getbbox();changed=count_changed(diff)
 if not plans or s['alpha']==1:assert box is None,(s['alpha'],box)
 else:
  assert box is not None
  l,r,t,bottom=bounds;x0=math.ceil(300+l*13.5-.5);x1=math.ceil(300+r*13.5-.5)
  assert x0<=box[0]<box[2]<=x1 and math.floor(t*13.5)<=box[1]<box[3]<=math.ceil(bottom*13.5)
 transition=count_changed(ImageChops.difference(a,previous)) if previous else None
 control_transition=count_changed(ImageChops.difference(b,previous_control)) if previous_control else None
 rows.append(dict(alpha=s['alpha'],changed_pixels=changed,bounds=box,portal=bounds,transition_pixels=transition,control_transition_pixels=control_transition))
 previous=a;previous_control=b
(p/'portal-replay-tests.json').write_text(json.dumps(dict(result='PASS',samples=rows,scope='Seventeen diagnostic samples; exact newer endpoint unchanged. Does not prove continuous smoothness or live integration.'),indent=2));print(rows)
