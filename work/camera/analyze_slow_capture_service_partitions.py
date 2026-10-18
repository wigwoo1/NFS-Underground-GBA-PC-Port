"""Audit all retained whole-run slow capture service partitions."""
import json,sys
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text());assert r['captures']==r['prepared']+r['fallback'];assert len(r['slow_retained'])==min(32,r['slow_total']);rows=[]
for p in r['slow_retained']:
 service=p['service_rows'];assert [x[0] for x in service]==['entry','service_lock_acquired','cv_wait_begin','cv_acquired','size_begin','cv_wait_begin','cv_acquired','buffer_selected']
 v=[x[1] for x in service];assert v==sorted(v) and p['begin_ns']<=v[0]<=v[-1]<=p['end_ns']
 size,capture=p['rows'];s=capture['native_stats'];assert size['begin_ns']<=size['end_ns']<=capture['begin_ns']<=capture['end_ns']<=p['end_ns'];assert len(s)==7 and s[0]>0
 parts={'outer_to_entry':v[0]-p['begin_ns'],'capture_lock':v[1]-v[0],'to_initial_cv':v[2]-v[1],'initial_cv':v[3]-v[2],'to_size':v[4]-v[3],'size_and_to_selection':v[5]-v[4],'selection_cv':v[6]-v[5],'buffer_selection':v[7]-v[6],'after_selection_to_end':p['end_ns']-v[7]}
 assert sum(parts.values())==p['end_ns']-p['begin_ns']
 rows.append(dict(refresh=p['refresh'],epoch=p['epoch'],whole_ms=(p['end_ns']-p['begin_ns'])/1e6,service_parts_ms={k:v/1e6 for k,v in parts.items()},native_copy_ms=(s[5]-s[4])*1000/s[0],native_copy_cycles=s[6],path=capture['phase']))
out=dict(result='PASS_RETAINED_SLOW_SERVICE_PARTITIONS',captures=r['captures'],slow_total=r['slow_total'],retained=len(rows),omitted_slow=max(0,r['slow_total']-len(rows)),rows=rows,scope='Exact additive service elapsed partitions for top32 >10ms calls; lock brackets include scheduler delay, do not prove contention. Whole counters complete, omitted slow events explicit; no physical scanout/cadence certification.')
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(out['result'],out['captures'],'captures',out['slow_total'],'slow');print(rows[0] if rows else 'No >10ms captures')
