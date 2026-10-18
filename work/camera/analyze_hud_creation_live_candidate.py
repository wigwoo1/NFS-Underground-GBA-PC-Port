import json,sys,statistics
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text());assert r['gc_trace_dropped']==0
rows=[x for x in r['presentation_samples'] if x.get('native_result')==1 and (x.get('prepared',{}).get('hud_lease_stages') or {}).get('creation_stages')];assert rows
parts={'validate':('start_ns','validated_ns'),'library_bind':('validated_ns','bound_ns'),'pointer':('bound_ns','copy_begin_ns'),'native_create':('copy_begin_ns','copied_ns')}
summary={k:dict(count=len(rows),median_ms=statistics.median(x['prepared']['hud_lease_stages']['creation_stages'][b]-x['prepared']['hud_lease_stages']['creation_stages'][a] for x in rows)/1e6,max_ms=max(x['prepared']['hud_lease_stages']['creation_stages'][b]-x['prepared']['hud_lease_stages']['creation_stages'][a] for x in rows)/1e6) for k,(a,b) in parts.items()}
slow=[]
for x in sorted(rows,key=lambda x:x['prepared']['source_prepare_ns'],reverse=True)[:5]:
 c=x['prepared']['hud_lease_stages']['creation_stages'];a,b=c['copy_begin_ns'],c['copied_ns']
 slow.append(dict(index=x['display_index'],stages_ms={k:(c[b]-c[a])/1e6 for k,(a,b) in parts.items()},native_create_gc_overlaps=[dict(generation=g['generation'],overlap_ms=(min(b,g['end_ns'])-max(a,g['start_ns']))/1e6) for g in r['gc_collection_samples'] if min(b,g['end_ns'])>max(a,g['start_ns'])]))
out=dict(result='RETAINED_HUD_CREATION_SETUP_NATIVE_SPLIT',stages=summary,slowest=slow,scope='Retained new snapshots only; native_create wall includes allocation/copy/lock and scheduling/GIL reacquisition, not exclusive native CPU or allocation proof.')
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
