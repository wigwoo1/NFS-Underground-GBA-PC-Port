from pathlib import Path
import struct,json
from scene_batches import records,batches
p=Path('work/camera');events=list(records(p/'motion-original-draw-pages-world.bin'));old=list(records(p/'motion-original-source-8750-8781.bin'));regular=[e for e in events if e['pc'] not in (0xffff0084,0x03003d4c,0x03005920)];assert len(regular)==len(old)
for a,b in zip(old,regular):assert a['pc']==b['pc'] and a['frame']==b['frame'] and a['regs']==b['regs']
ids={e['id']:o['id'] for o,e in zip(old,regular)};pending={};draws={};unassigned=[];assets=p/'motion-draw-page-assets';assets.mkdir(exist_ok=True)
for e in events:
 if e['pc']==0xffff0084:
  meta=struct.unpack('<11I',e['blocks'][85][1]);stage,identity,pc=meta[:3]
  if stage==0:pending[identity]=dict(pc=pc,before=e['blocks'][84][1]);unassigned.append(identity)
  elif stage==1:
   d=pending.pop(identity);d['after']=e['blocks'][84][1];d['metadata']=list(meta);assert 'event' in d;draws[d['event']]=d
  continue
 if e['pc'] in (0x030032f0,0x03000304,0x03004770):
  identity=unassigned.pop();pending[identity]['event']=ids[e['id']]
for eid,d in draws.items():
 for kind in ('before','after'):
  target=assets/(str(eid)+'-'+kind+'.bin');target.write_bytes(d.pop(kind));d[kind+'_path']=str(target)
r=dict(result='CAPTURED_ACTUAL_DRAW_FRAMEBUFFERS',existing_source_records_preserved=len(old),draws={str(k):v for k,v in draws.items()},completed_draws=len(draws),pending_unclosed=len(pending),scope='Exact original draw-entry/return VRAM snapshots and source event linkage. FinalRAM unchanged; actual draw pixel parity remains next.')
(p/'motion-draw-page-tests.json').write_text(json.dumps(r,indent=2),encoding='utf-8');print(r['result'],len(draws),len(pending))
