"""Associate traffic image checks with actual accepted display/update records."""
from pathlib import Path
import json,csv,re,sys
def verify_traffic(session_path):
 session=json.loads(Path(session_path).read_text(encoding='utf-8-sig'));log=Path(session['log']).read_text();rows=list(csv.DictReader(Path(session['display_trace']).open()));records=[]
 events=re.findall(r'early_gpu_pixel_models=(\d+) target=([0-9.]+) updates=(\d+)',log)
 assert events and len(events)==int(re.search(r'early_gpu_verified=(\d+)',log)[1])
 for models,target,updates in events:
  matching=[row for row in rows if abs(float(row['target'])-float(target))<1e-9]
  assert len(matching)==1
  row=matching[0];assert int(models)>=2 and int(updates)>0 and int(row['display_simulation_steps'])==int(updates)
  assert int(row['ready'])==1 and int(row['early_gpu_reused'])==1 and int(row['epoch_mismatch'])==0
  assert int(row['source_older_refresh'])<=float(target)<=int(row['source_newer_refresh'])
  records.append(dict(models=int(models),target=float(target),display_index=int(row['display_index']),original_updates=int(updates),older_scene=int(row['older']),newer_scene=int(row['newer']),older_refresh=int(row['source_older_refresh']),newer_refresh=int(row['source_newer_refresh'])))
 return records
if __name__=='__main__':
 records=verify_traffic(sys.argv[1]);print(json.dumps(dict(result='PASS',samples=records),indent=2))
