import json,re,sys,subprocess,hashlib,shutil
from pathlib import Path
p=Path('work/camera');manifest=p/'prototype-runs/matched-gl-sync-1791455237680475500/manifest.json';rows=json.loads(manifest.read_text());assert len(rows)==2 and [x['enabled'] for x in rows]==[False,True] and all(x['exit_code']==0 for x in rows)
assert len(set(x['binary_sha256'] for x in rows))==1 and hashlib.sha256((p/'owned-gpu-gl-display-cadence-candidate.dll').read_bytes()).hexdigest()==rows[0]['binary_sha256']
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/matched-gl-sync-20261008');cp.mkdir(exist_ok=True);summaries=[]
for item in rows:
 folder=cp/('enabled' if item['enabled'] else 'disabled');folder.mkdir(exist_ok=True);log=Path(item['log']).read_text()
 def find(prefix):return str(p/'prototype-runs'/re.search(prefix+r'-\d+\.json',log).group())
 for script,args in [('audit_playable_launcher_run.py',[find('owned-native'),find('pool-cleanup'),str(folder)]),('verify_prototype_game_state_replay.py',[find('owned-native'),str(folder)]),('analyze_gl_display_cadence_candidate.py',[find('gl-display-cadence'),str(folder/'cadence.json')])]:subprocess.run([sys.executable,str(p/script),*args],check=True,stdout=subprocess.DEVNULL)
 report=json.loads(Path(find('owned-native')).read_text());cadence=json.loads((folder/'cadence.json').read_text());assert cadence['swap_intervals']==[int(item['enabled'])]
 summaries.append(dict(enabled=item['enabled'],report=find('owned-native'),original_updates=report['original_updates'],presentations=report['presentations'],cadence=cadence))
 shutil.copy2(Path(find('gl-display-cadence')),folder/Path(find('gl-display-cadence')).name)
(cp/'comparison.json').write_text(json.dumps(summaries,indent=2));shutil.copytree(manifest.parent,cp/'harness',dirs_exist_ok=True)
for n in ['run_matched_gl_sync_comparison.py','run_playable_gl_cadence_candidate.py','analyze_gl_display_cadence_candidate.py']:shutil.copy2(p/n,cp/n)
for r in summaries:print({k:v for k,v in r.items() if k!='cadence'}, {k:r['cadence'][k] for k in ['swap_bracket_median_ms','swap_bracket_max_ms','probe_cost_total_ms']})
