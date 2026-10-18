import json
from pathlib import Path
raw=Path('work/camera/prototype-runs/owned-native-1791634635935718400.json');r=json.loads(raw.read_text());u=r['original_update_retention']['complete_original_updates'];updates=u['records'];assert u['dropped']==0 and u['total']==len(updates)==507
assert all(b['refresh']==a['refresh']+1 for a,b in zip(updates,updates[1:]))
assert all(x['completed_ns']>=x['started_ns'] for x in updates)
p=r['producer_retention'];scenes=r['producer_cycle_samples'];assert p['dropped_records']==0 and len(scenes)==p['total_records']==137
stage_names=list(scenes[0]['stages']);totals={name:sum(x['stages'][name] for x in scenes)/1e6 for name in stage_names}
late=[x['started_ns']-x['original_deadline_ns'] for x in updates];busy=[x['completed_ns']-x['started_ns'] for x in updates]
ledger=Path('work/camera/prototype-runs/expired-admission-1791634636153856000.json');m=json.loads(ledger.read_text());assert m['stats']['dropped_records']==0
lookup={x['refresh']:x for x in updates};joined=[]
for row in m['records']:
 source=lookup.get(row['newer']);assert source is not None
 joined.append(dict(source_already_late_ns=source['completed_ns']-row['deadline_ns'],after_source_ns=row['native'][5]-source['completed_ns']))
q=r['submit_retention']['whole_submission_space_wait'];assert q['dropped']==0
out=dict(queue_space_wait_total_ms=q['total_ns']/1e6,queue_space_wait_max_ms=q['max_ns']/1e6,queue_wait_fraction_of_worker_submit=q['total_ns']/1e6/totals['worker_submit_ns'],result='PASS_COMPLETE_PRODUCER_BACKLOG_AUDIT',raw=str(raw.resolve()),updates=len(updates),scenes=len(scenes),first_update_late_ms=late[0]/1e6,last_update_late_ms=late[-1]/1e6,max_update_late_ms=max(late)/1e6,update_elapsed_ms=(updates[-1]['completed_ns']-updates[0]['started_ns'])/1e6,scheduled_update_span_ms=(updates[-1]['original_deadline_ns']-updates[0]['original_deadline_ns'])/1e6,total_update_busy_ms=sum(busy)/1e6,producer_scene_stage_totals_ms=totals,retired_source_joins=len(joined),source_already_late_count=sum(x['source_already_late_ns']>0 for x in joined),max_source_display_deadline_late_ms=max(x['source_already_late_ns'] for x in joined)/1e6,scope='Complete507originalupdate and137producer-scene ledgers;504exactrefresh joins toretired newer endpoints. Update/source labels from actual run, no independent game-clock recalibration. Stage totals are measured scopes, not additive exclusive CPU attribution; source timing alone does not prove every lost slot was caused by producer work. Cadence/game timing remain failed/unqualified.')
Path('outputs/nfsug-native-renderer/camera-research/checkpoints/all-successful-native-starvation-20261010/producer-backlog-audit.json').write_text(json.dumps(out,indent=2));print(out['result']);print(totals)

