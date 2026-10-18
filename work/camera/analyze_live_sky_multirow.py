"""Join bounded live readbacks to actual committed draws; report occlusion limits."""
import json,sys
from pathlib import Path
capture=Path(sys.argv[1]);report=Path(sys.argv[2]);out=Path(sys.argv[3])
a=json.loads(capture.read_text());r=json.loads(report.read_text());assert not a['errors']
lookup={x['sample_begin_ns']:x for x in r['presentation_samples'] if x.get('native_committed_sample')}
counts=[];eligible=changed=strong=strong_changed=0;previous_by_row={};row_counts={};misses=[]
for c in a['captures']:
 sky_row=c['sky_row'];prev=previous_by_row.get(sky_row)
 row_counts[sky_row]=row_counts.get(sky_row,0)+1
 row=lookup[c['draw_started_ns']];assert c['weight']==row['sky_fraction']
 x=bytes.fromhex(c['actual']);e=bytes.fromhex(c['expected']);assert len(x)==len(e)==720
 mask=[max(abs(x[i+k]-e[i+k]) for k in range(3))<=1 for i in range(0,720,3)];counts.append(sum(mask))
 if prev:
  px,pe,pm,pr=prev
  if row['epoch']==pr['epoch'] and row['display_index']==pr['display_index']+1:
   for j in range(240):
    i=j*3;delta=max(abs(e[i+k]-pe[i+k]) for k in range(3))
    if mask[j] and pm[j] and delta:
     eligible+=1;changed+=x[i:i+3]!=px[i:i+3]
     if x[i:i+3]==px[i:i+3]:misses.append(dict(sky_row=sky_row,column=j,display_index=row["display_index"],expected_delta=delta,actual=list(x[i:i+3]),expected_before=list(pe[i:i+3]),expected_after=list(e[i:i+3])))
     if delta>=4:strong+=1;strong_changed+=x[i:i+3]!=px[i:i+3]
 previous_by_row[sky_row]=(x,e,mask,row)
passed=bool(eligible and changed==eligible and strong_changed==strong)
result=dict(result='PASS_BOUNDED_LIVE_PIXEL_MOTION' if passed else 'FAILED_PIXEL_CHANGE_CHECK',misses=misses,captures=len(counts),sky_rows=row_counts,committed_timestamp_and_weight_matches=len(counts),matched_centers_min=min(counts),matched_centers_max=max(counts),expected_moving_matched_centers=eligible,actual_changed_centers=changed,expected_strong_changes=strong,actual_strong_changes=strong_changed,scope='Selected draw target nine sky rows before presentation; only centers matching expected source/palette color within1 both adjacent frames included. Foreground/coverage and coincidental color matches prevent independent fullsky fidelity proof. Readback instrumentation changes timing; no cadence/scanout certification.')
out.write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
