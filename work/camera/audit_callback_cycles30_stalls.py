import json,struct
from pathlib import Path
cp=Path(r'G:\EXTRA DATA DRIVE\Desktop\Games\Codex\NFSUG-Native-PC-Port\outputs\nfsug-native-renderer\camera-research\checkpoints\vertex-conversion-profile-20261010');out=[]
for label in ('callback-cycles30',):
 r=json.loads((cp/(label+'-raw.json')).read_text());jobs={(j['older'],j['newer']):j for j in r['world_preparation_stage_samples']}
 for w in r['live_observation_stats']['whole_run_api_intervals']['native_commit_long_intervals']['records']:
  tx=w['transaction'];pair=tuple(tx['commit'][2:4]);j=jobs[pair];t=j['terminal'][5];s=w['caller_stages'];d=w['caller_timing'];p=w['prepared'];dispatch=p['renderer_dispatch'];deadline=tx['wait'][1];first=t['sample_transfer_rows'][0]['ready_ns'];published=j['parent_sample_rows'][0]['published_ns'];assert first<=published
  out.append(dict(label=label,pair=pair,index=w['display_index'],alpha=struct.unpack('<d',struct.pack('<Q',tx['commit'][5]))[0],gap_ms=w['interval_ns']/1e6,first_sample_ready_before_deadline_ms=(deadline-first)/1e6,first_sample_published_before_take_ms=(s['preparation_take_begin_ns']-published)/1e6,parent_take_ms=(s['preparation_take_end_ns']-s['preparation_take_begin_ns'])/1e6,hud_wait_ms=(s['hud_prefetch_wait_end_ns']-s['hud_prefetch_wait_begin_ns'])/1e6,draw_ms=(d['draw_end_ns']-d['draw_begin_ns'])/1e6,renderer_dispatch=dispatch,consumer_stages=p['consumer_stages'],hud_lease=p['hud_lease_stages'],present_ms=(d['present_end_ns']-d['present_begin_ns'])/1e6))
(cp/'callback-cycles30-stall-renderer-joins.json').write_text(json.dumps(dict(rows=out,scope='Firstsample readiness only; no laterfraction publication identity is implied. Elapsed stage overlap not exclusive CPU causality.'),indent=2));print(json.dumps([{k:v for k,v in x.items() if k not in ('consumer_stages','hud_lease')} for x in out],indent=2))

