import json,sys,re,subprocess,statistics
from pathlib import Path
manifest=Path(sys.argv[1]);records=json.loads(manifest.read_text());assert len(records)==2 and records[0]['binary_sha256']==records[1]['binary_sha256'];results=[]
for item in records:
 assert item['exit_code']==0
 log=Path(item['log']).read_text();names={}
 for line in log.splitlines():
  path=Path(line.strip())
  for prefix in ['owned-native-','pool-cleanup-','prepared-transfers-','source-dxgi-stages-','display-observations-']:
   if path.name.startswith(prefix) and path.suffix=='.json':names[prefix]=path
 assert len(names)==5,names
 cp=manifest.parent/('enabled-audit' if item['enabled'] else 'disabled-audit');cp.mkdir(exist_ok=True)
 rp=names['owned-native-'];r=json.loads(rp.read_text())
 for script,args in [('audit_playable_launcher_run.py',[rp,names['pool-cleanup-'],cp]),('verify_prototype_game_state_replay.py',[rp,cp]),('analyze_prepared_stalls_candidate.py',[rp,names['prepared-transfers-'],names['source-dxgi-stages-'],cp/'stalls.json'])]:
  with (cp/(script+'.txt')).open('w') as out:subprocess.run([sys.executable,str(Path('work/camera')/script)]+list(map(str,args)),stdout=out,stderr=subprocess.STDOUT,check=True)
 observation=json.loads(names['display-observations-'].read_text());assert bool(observation['rows'])==item['enabled'] and not observation['dropped']
 cadence=json.loads((cp/'sky-cadence.json').read_text());stalls=json.loads((cp/'stalls.json').read_text());rows=[x for x in r['presentation_samples'] if x.get('native_committed_sample')];lateness=[(x['native_committed_sample'][6]-x['presentation_deadline_ns'])/1e6 for x in rows]
 results.append(dict(enabled=item['enabled'],report=str(rp),original_updates=r['original_updates'],presentations=r['presentations'],cpu_cadence_gate=cadence['cpu_cadence_gate'],first120_end_late_ms=statistics.median(lateness[:120]),last120_end_late_ms=statistics.median(lateness[-120:]),phase_summary=stalls['phase_summary'],observation_records=len(observation['rows'])))
out=dict(result='PASS_MATCHED_BINARY_OBSERVATION_COMPARISON',runs=results,scope='Sequential identical binary/flags except startup observation toggle; external load uncontrolled, no exclusive causality or display certification.')
(manifest.parent/'comparison.json').write_text(json.dumps(out,indent=2));print(out)
