import json,sys,statistics
from pathlib import Path
r,p,f=[json.loads(Path(x).read_text()) for x in sys.argv[1:4]];assert not p['dropped']
s=[x for x in r['presentation_samples'] if x.get('presentation_backend')=='dxgi_flip_sequential'];assert len(s)==len(f['rows'])
preps={tuple(x[:3]):x for x in p['rows']};rows=[]
names=['setup_get_buffer','interop_lock','gl_blit','interop_unlock','resource_copy','prepare_tail','restore_cleanup']
for x,y in zip(s,f['rows']):
 z=preps.pop((x['epoch'],x['generation'],x['display_index']))
 assert z[19]==y[16]==0 and len(z)==21 and len(y)==18
 assert list(z[3:11])==sorted(z[3:11]) and list(y[:8])==sorted(y[:8])
 assert x['draw_complete_ns']<=z[3]<=z[10]<=x['native_commit_stage_ns'][0]<=y[0]<=y[7]<=x['native_commit_stage_ns'][4]
 phases={name:dict(wall_ms=(z[4+i]-z[3+i])/1e6,thread_cycles=z[12+i]-z[11+i]) for i,name in enumerate(names)}
 rows.append(dict(epoch=x['epoch'],generation=x['generation'],index=x['display_index'],refresh=x['refresh'],transfer_ms=(z[10]-z[3])/1e6,transfer_cycles=z[18]-z[11],phases=phases,present_call_ms=(y[6]-y[5])/1e6,present_transaction_ms=(y[7]-y[0])/1e6,present_thread_cycles=y[15]-y[8]))
assert rows
summary={n:dict(total_ms=sum(x['phases'][n]['wall_ms'] for x in rows),median_ms=statistics.median(x['phases'][n]['wall_ms'] for x in rows),max_ms=max(x['phases'][n]['wall_ms'] for x in rows),over_20ms=sum(x['phases'][n]['wall_ms']>20 for x in rows)) for n in names}
out=dict(result='PASS_EXACT_PREPARED_STALL_ATTRIBUTION',checked=len(rows),uncommitted=len(preps),phase_summary=summary,present_call_total_ms=sum(x['present_call_ms'] for x in rows),largest_transfers=sorted(rows,key=lambda x:x['transfer_ms'],reverse=True)[:20],largest_present_calls=sorted(rows,key=lambda x:x['present_call_ms'],reverse=True)[:10],scope='Exact frame identity and transfer/finalcommit containment. Phase wall time and thread execution cycles are reported separately; scheduling/driver/GPU waits are not exclusively classified.')
Path(sys.argv[4]).write_text(json.dumps(out,indent=2));print({k:v for k,v in out.items() if k not in ['largest_transfers','largest_present_calls']});print('largest transfer',out['largest_transfers'][0]);print('largest present',out['largest_present_calls'][0])
