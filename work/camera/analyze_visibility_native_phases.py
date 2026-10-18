import json,sys
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text());assert not r['dropped'];rows=[]
for x in r['records']:
 p=next(s for s in x['stages'] if s['name']=='native_call')
 matches=[n for n in r['native_records'] if p['started_ns']<=n['started_ns']<=n['completed_ns']<=p['completed_ns']]
 assert len(matches)==1 and matches[0]['count']==x['count']
 n=matches[0];rows.append(dict(count=x['count'],started_ns=x['started_ns'],wall_ms=(x['completed_ns']-x['started_ns'])/1e6,diagnostic_setup_unassigned_ms=(x['stages'][0]['started_ns']-x['started_ns'])/1e6,phases=[dict(name=s['name'],ms=(s['completed_ns']-s['started_ns'])/1e6,cycles=s['thread_cycles']) for s in x['stages']],native_inside_ms=n['native_ns']/1e6,native_wrapper_ms=n['wrapper_ns']/1e6,native_cycles=n['native_cycles'],gc_collections_changed=x['gc_collections_before']!=x['gc_collections_after']))
out=dict(result='PASS_MATCHED_VISIBILITY_PHASES',count=len(rows),largest=sorted(rows,key=lambda x:x['wall_ms'],reverse=True)[:5],scope=r['scope']);Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))

