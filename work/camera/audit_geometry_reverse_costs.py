import json,re,statistics
from pathlib import Path
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/all-successful-native-starvation-20261010');rows=[]
for label in ('candidate','baseline'):
 raw=re.findall(r'G:[^\r\n]*owned-native-\d+\.json',(cp/('geometry-reverse-'+label+'.log')).read_text())[-1]
 report=json.loads(Path(raw).read_text());jobs=report['world_preparation_stage_samples'];metrics={k:[] for k in ('pack','copy','deserialize','parent_restore')};sizes=[]
 for job in jobs:
  parent=job['parent_start_timing'];metrics['pack'].append((parent['packed_ns']-parent['pack_begin_ns'])/1e6);sizes.append(parent['input_bytes'])
  profile=job['terminal'][5]['input_read_profile'];assert profile is not None and profile['begin_ns']<=profile['copied_ns']<=profile['decoded_ns']
  metrics['copy'].append((profile['copied_ns']-profile['begin_ns'])/1e6);metrics['deserialize'].append((profile['decoded_ns']-profile['copied_ns'])/1e6)
  for sample in job['parent_sample_rows']:
   metrics['parent_restore'].append((sample['decoded_ns']-sample['received_ns'])/1e6)
 rows.append(dict(variant=label,jobs=len(jobs),median_input_bytes=statistics.median(sizes),timings={k:dict(median_ms=statistics.median(v),max_ms=max(v),samples=len(v)) for k,v in metrics.items()}))
out=dict(result='PASS_REVERSE_GEOMETRY_INPUT_COST_ACCOUNTING',rows=rows,scope='Completed-job wall scopes; inclusive and subject to scheduling, not exclusive CPU or all retired-job coverage.')
(cp/'geometry-reverse-input-costs.json').write_text(json.dumps(out,indent=2));print(out)
