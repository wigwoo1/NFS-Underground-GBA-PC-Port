"""Measure original wall value changes against raw and source raster support bounds."""
import hashlib,json,struct,sys
from pathlib import Path
import numpy as np
from scene_batches import batches
report_path=Path(sys.argv[1]);report=json.loads(report_path.read_text());trace=Path(report['trace']);assert hashlib.sha256(trace.read_bytes()).hexdigest()==report['trace_sha256'];checks=[]
for batch in batches(trace):
 pending={};wall=None
 for event in batch['events']:
  if event['pc']==0x03000304:
   wall=(event['blocks'][5][0],struct.unpack_from('<4H',event['blocks'][1][1],226))
   if pending:
    identity=next(reversed(pending));before,bounds,source=pending[identity];assert source==wall[0];pending[identity]=(before,wall[1],source)
  if event['pc']!=0xffff0084:continue
  stage,identity,pc,lr,sp,state,source,dispcnt=struct.unpack('<8I',event['blocks'][85][1][:32])
  if pc!=0x03000304:continue
  image=np.frombuffer(event['blocks'][84][1],np.uint8);start=batch['display_page']*0xa000
  if stage==0:
   pending[identity]=(image[start:start+38400].copy(),None,source);continue
  if identity not in pending:continue
  before,bounds,source=pending.pop(identity);assert bounds is not None;mask=(before!=image[start:start+38400]).reshape(160,240);l,r,t,b=bounds
  y,x=np.indices((160,240));raw=(x>=l)&(x<r)&(y>=t)&(y<b)
  # Original horizontal halfword columns include the clip-right column;
  # vertical source span clips inclusive bottom and writes one terminal row.
  effective=(l//2*2,min(240,r//2*2+2),t,min(160,b+2));el,er,et,eb=effective
  support=(x>=el)&(x<er)&(y>=et)&(y<eb)
  checks.append(dict(interval=[batch['begin_refresh'],batch['end_refresh']],draw_id=identity,source=hex(source),bounds=bounds,raster_support_bounds=effective,changed=int(mask.sum()),outside_raw=int((mask&~raw).sum()),outside_source_support=int((mask&~support).sum())))
assert len(checks)>=48
out=report_path.with_name(report_path.stem.replace('-verification','-wall-portal-coverage')+'.json');out.write_text(json.dumps(dict(result='MEASURED',checks=checks,scope='Actual original displayed-page value changes against captured wall bounds and halfword-column/inclusive-terminal-row support. Identical-value writes unobservable; does not prove continuous 4K geometry should copy GBA quantization.'),indent=2));print(json.dumps(dict(walls=len(checks),changed=sum(c['changed'] for c in checks),outside_raw=sum(c['outside_raw'] for c in checks),outside_source_support=sum(c['outside_source_support'] for c in checks))))
