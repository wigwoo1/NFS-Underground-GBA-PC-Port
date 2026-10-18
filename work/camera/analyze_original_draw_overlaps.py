"""Value-change attribution in flip-closed original scenes; no write-coverage claim."""
import json,struct,sys
from pathlib import Path
import numpy as np
from scene_batches import batches
report_file=Path(sys.argv[1]);report=json.loads(report_file.read_text());trace=Path(report['trace']);scenes=[]
for batch in batches(trace):
 pending={};model_mask=np.zeros(0x18000,dtype=bool);checks=[];model_object=None;model_context=None;entries=0;captured_entries=0
 for event in batch['events']:
  if event['pc']==0x03002628:
   model_object=event['blocks'][62][0];model_context=event['blocks'][64][0]
  if event['pc'] in (0x030032f0,0x03000304,0x03004770):entries+=1
  if event['pc']!=0xffff0084:continue
  meta=struct.unpack('<8I',event['blocks'][85][1][:32]);stage,identity,pc,lr,sp,state,source,dispcnt=meta
  assert dispcnt&7==4,'Displayed-byte attribution requires mode4'
  image=np.frombuffer(event['blocks'][84][1],np.uint8)
  if stage==0:
   captured_entries+=1
   if pc==0x03004770:assert model_context==source,'Model invocation context mismatch'
   pending[identity]=(meta,image.copy(),model_object if pc==0x03004770 else None);continue
  if identity not in pending:continue # Entry before this completed interval.
  before_meta,before,object_address=pending.pop(identity);changed=before!=image
  page=batch['display_page'];begin=page*0xa000;end=begin+240*160
  visible=changed[begin:end];overlap=visible&model_mask[begin:end]
  if pc==0x03004770:model_mask|=changed
  else:model_mask&=~changed
  coords=np.flatnonzero(overlap)
  checks.append(dict(draw_id=identity,pc=hex(pc),state=hex(state),source=hex(source),closure='page_flip' if stage==2 else 'model_epilogue' if pc==0x03004770 else 'routine_return',model_object=None if object_address is None else hex(object_address),visible_changed_pixels=int(visible.sum()),later_world_over_model_pixels=0 if pc==0x03004770 else int(overlap.sum()),overlap_samples=[] if pc==0x03004770 else [[int(i%240),int(i//240)] for i in coords[:16]]))
 if checks:scenes.append(dict(begin_refresh=batch['begin_refresh'],end_refresh=batch['end_refresh'],display_page=batch['display_page'],draws=checks,original_routine_entries=entries,captured_entries=captured_entries,all_observed_routines_captured=entries==captured_entries and not pending,incomplete_entries=list(pending)))
assert scenes
world=[c for s in scenes for c in s['draws'] if c['pc']!='0x3004770']
out=report_file.with_name(report_file.stem.replace('-verification','-overlaps')+'.json')
result=dict(result='ANALYZED',source_report=str(report_file),scenes=scenes,world_over_model_changed_pixels=sum(c['later_world_over_model_pixels'] for c in world),scope='Mode4 displayed-page byte value differences for matched original routine entry/return snapshots in flip-closed scenes. Model changed-pixel ownership cleared when later world value changes. Identical-value writes and unmatched/truncated draw intervals excluded; not complete write coverage or native fidelity proof.')
out.write_text(json.dumps(result,indent=2));print(json.dumps(dict(report=str(out),completed_scenes=len(scenes),overlap_draws=sum(bool(c['later_world_over_model_pixels']) for c in world),overlap_pixels=result['world_over_model_changed_pixels'])))
