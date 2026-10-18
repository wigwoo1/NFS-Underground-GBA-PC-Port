import json,sys,collections,statistics
from pathlib import Path
p,c=[json.loads(Path(x).read_text()) for x in sys.argv[1:3]];assert not p['dropped'] and not c['dropped'];prep={tuple(x[:3]):x for x in p['rows']};rows=[]
for x in c['rows']:
 assert len(x)==15 and x[7]==x[8]==2 and x[13]==x[14]==0
 assert all(v in (0x911a,0x911b,0x911c) for v in x[3:7])
 t=prep.pop(tuple(x[:3]));assert t[19]==0
 rows.append(dict(identity=x[:3],world_before=hex(x[3]),world_after=hex(x[4]),blit_before=hex(x[5]),blit_after=hex(x[6]),poll_ns=list(x[9:13]),lock_ms=(t[5]-t[4])/1e6,unlock_ms=(t[7]-t[6])/1e6,lock_thread_cycles=t[13]-t[12],unlock_thread_cycles=t[15]-t[14]))
assert rows and not prep
counts={n:dict(collections.Counter(x[n] for x in rows)) for n in ['world_before','world_after','blit_before','blit_after']};long=[x for x in rows if max(x['lock_ms'],x['unlock_ms'])>20]
out=dict(result='PASS_EXACT_GPU_COMPLETION_PHASE_JOIN',transfers=len(rows),created=sum(x[7] for x in c['rows']),deleted=sum(x[8] for x in c['rows']),status_counts=counts,long_waits=len(long),maximum_poll_ns=max(v for x in rows for v in x['poll_ns']),total_poll_ms=sum(v for x in rows for v in x['poll_ns'])/1e6,long_wait_records=sorted(long,key=lambda x:max(x['lock_ms'],x['unlock_ms']),reverse=True),scope='Zero-timeout fence snapshots before/after sharing calls, with explicit diagnostic glFlush. Pending-to-signaled proves completion occurred within interval, not which GPU/driver/scheduler cause dominated wall duration.')
Path(sys.argv[3]).write_text(json.dumps(out,indent=2));print({k:v for k,v in out.items() if k!='long_wait_records'});print('Largest',out['long_wait_records'][:2])
