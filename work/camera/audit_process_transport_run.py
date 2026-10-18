"""Audit actual child transport activation, timing and owned-resource shutdown."""
import argparse,json,statistics,runpy,sys,shutil
from pathlib import Path
from analyze_live_sky_cadence import analyze
from verify_pause_replay_commits import verify
p=argparse.ArgumentParser();p.add_argument('report');p.add_argument('pool');p.add_argument('destination');p.add_argument('--dedup',action='store_true');o=p.parse_args()
rp=Path(o.report);pp=Path(o.pool);cp=Path(o.destination);cp.mkdir(exist_ok=True);r=json.loads(rp.read_text());jobs=r['world_preparation_stage_samples'];writes=[j['child_stages']['shared_write'] for j in jobs];reads=[j['shared_read'] for j in jobs]
assert writes and all(w['deduplication_enabled']==o.dedup for w in writes)
for j,w,v in zip(jobs,writes,reads):
 b=j['child_stages']['child_boundaries'];assert b['encoded_ns']<=w['begin_ns']<=w['end_ns']<=v['begin_ns']<=v['end_ns']<=b['sent_ns'];assert w['payload_bytes']==v['payload_bytes'];assert w['thread_cycles']>=0 and v['thread_cycles']>=0
cost=dict(jobs=len(jobs),child_deduplication_enabled=o.dedup,payload_bytes=sum(w['payload_bytes'] for w in writes),write_median_ms=statistics.median((w['end_ns']-w['begin_ns'])/1e6 for w in writes),read_median_ms=statistics.median((v['end_ns']-v['begin_ns'])/1e6 for v in reads),ack_wait_median_ms=statistics.median((j['child_stages']['child_boundaries']['sent_ns']-w['end_ns'])/1e6 for j,w in zip(jobs,writes)),scope='Observed wall intervals include scheduling; ack wait includes parent copy and notifications')
sky=analyze(r)
for name,value in [('transport-cost',cost),('sky-cadence',sky),('pause-replay',verify(r))]:(cp/(name+'.json')).write_text(json.dumps(value,indent=2))
for script,out in [('verify_native_pause_ack.py','pause-ack.json'),('verify_original_update_deadlines.py','original-timing.json')]:sys.argv=[script,str(rp),str(cp/out)];runpy.run_path(str(Path(__file__).parent/script),run_name='__main__')
s=r['shutdown_evidence'];p=s['preparation_service_shutdown'];assert not s['gpu_thread_alive'] and not s['preparation_thread_alive'] and s['native_owner_released'];assert not p['child_alive'] and p['child_exitcode']==0 and not p['forced_termination'] and p['shared_mapping_closed'] and p['connection_closed'] and not p['retained_previous_scene']
for k in ('gpu_queries_after_close','gpu_fences_after_close','active_contexts_after_close','retained_scene_count','pending_scene_count','prepared_result_count'):assert s[k]==0
pool=json.loads(pp.read_text());assert pool['targets']==[0]*5 and pool['fences'][0]==pool['fences'][1] and pool['fences'][3]==0
for path in (rp,pp,Path(__file__)):shutil.copy2(path,cp/path.name)
(cp/'cleanup-audit.json').write_text(json.dumps(dict(result='PASS',shutdown=s,pool=pool),indent=2))
summary=dict(updates=r['original_updates'],scenes=r['owned_scene_submissions'],rows=r['presentations'],cost=cost,cadence=sky['active_presentation_cadence']);(cp/'summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary))
