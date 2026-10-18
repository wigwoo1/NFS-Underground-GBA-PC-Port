"""Join segmented draw stage records to live committed samples."""
import json, sys
from pathlib import Path

def analyze(report,trace):
 assert trace['dropped']==0,'Draw trace overflow prevents complete coverage'
 source=[x for x in report['presentation_samples'] if x.get('native_draw_boundary')]
 rows=trace['rows'];indexed={tuple(x[12:15]):x for x in rows};assert len(indexed)==len(rows);assert all(tuple(x['native_draw_boundary'][:3]) in indexed for x in source);uncommitted=[x for x in rows if tuple(x[12:15]) not in {tuple(y['native_draw_boundary'][:3]) for y in source}]
 records=[]
 for sample in source:
  row=indexed[tuple(sample['native_draw_boundary'][:3])]
  assert row[12:15]==sample['native_draw_boundary'][:3] and row[15]==0
  assert row[0]<=row[12]<=row[4]<=row[5]<=row[6]<=row[7]<=row[13]<=row[1]
  assert row[2]<=row[8]<=row[9]<=row[10]<=row[11]<=row[3]
  assert rows[row[17]-1]==row
  stages={name:dict(wall_ms=(row[5+i]-row[4+i])/1e6,thread_cycles=row[9+i]-row[8+i]) for i,name in enumerate(['sky','geometry','HUD'])}
  stages['outside_main_stages']=dict(wall_ms=((row[1]-row[0])-(row[7]-row[4]))/1e6,thread_cycles=(row[3]-row[2])-(row[11]-row[8]))
  records.append(dict(display_index=sample['display_index'],older=sample.get('older'),newer=sample.get('newer'),callback_wall_ms=(row[1]-row[0])/1e6,callback_thread_cycles=row[3]-row[2],stages=stages))
 return dict(result='PASS_COMPLETE_DRAW_STAGE_COVERAGE',callbacks=len(records),traced_callbacks=len(rows),uncommitted_draws=uncommitted,largest=sorted(records,key=lambda x:x['callback_wall_ms'],reverse=True)[:24],scope='Sky, geometry and HUD main function stage elapsed times and thread execution cycles; outside includes validation/input/setup/fences. CPU command submission includes driver waits; not GPU execution time or physical scanout proof.')
if __name__=='__main__':
 rp,tp,out=map(Path,sys.argv[1:4]);data=analyze(json.loads(rp.read_text()),json.loads(tp.read_text()));out.write_text(json.dumps(data,indent=2));print(json.dumps(dict(result=data['result'],callbacks=data['callbacks'],largest=data['largest'][:3]),indent=2))
