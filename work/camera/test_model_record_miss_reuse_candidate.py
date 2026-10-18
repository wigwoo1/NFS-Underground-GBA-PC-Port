import json,copy
from pathlib import Path
import owned_model_key_records_candidate as m
root=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/live-source-context-20261007/failure-snapshot')
frames=[(root/(label+'.frame.bin')).read_bytes() for label in ('older','newer')]
retained=json.loads(Path('work/camera/prototype-runs/owned-native-1791267744113946700.json').read_text())
frames.extend(Path(x['regenerated']).read_bytes() for x in retained['wall_diagnostic_frames'])
def normalized(r):return (r['refresh'],r['epoch'],r['ticks'],[(x['kind'],x['context'],x['key'],tuple(bytes(b) for b in x['blocks'])) for x in r['records']])
expected=[normalized(m.records(f)) for f in frames]
import owned_model_record_miss_reuse_install_candidate
checks=[]
for i,f in enumerate(frames):
 m._model_record_cache.entries=[]
 a=m.records(f);assert normalized(a)==expected[i]
 a['records'][0]['blocks'].clear();a['records'][0]['kind']=-1
 b=m.records(f);assert normalized(b)==expected[i] and b is not a
 mutable=bytearray(f);assert normalized(m.records(mutable))==expected[i]
 mutable[0]=0
 try:m.records(mutable)
 except ValueError:pass
 else:raise AssertionError('Invalid mutable envelope accepted')
 checks.append(dict(refresh=b['refresh'],records=len(b['records']),exact_metadata=True,caller_mutation_isolated=True,mutable_revalidated=True))
out=dict(result='PASS_MODEL_RECORD_MISS_REUSE',checks=checks,scope='Actual retained endpoint and16scene frames; full metadata blocks and model keys exact. No pixel/cadence claim.')
Path('work/camera/prototype-runs/model-record-miss-reuse-20261010.json').write_text(json.dumps(out,indent=2));print(out)
