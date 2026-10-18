import runpy,json
from pathlib import Path
from owned_source_process_service_candidate import encode_samples
baseline=runpy.run_path('work/camera/owned_source_process_service_candidate.py.before-prefix-reuse')['encode_samples']
source=Path('work/camera/test_precomputed_source_eight_samples.py').read_text();ns={};exec(source[:source.index(' import gc')]+'\nfinally: pass\n',ns)
owner=ns['cached'];samples=dict(owner.samples);owner.close();ns['history'].close();checks=[]
for borrowed in (False,True):
 old=baseline(samples,borrow_tails=borrowed);new=encode_samples(samples,borrow_tails=borrowed)
 assert old==new
 prefixes=[v[0] for a,v in new['samples']];assert len({id(v) for v in prefixes})==len(set(prefixes))
 assert all(type(v) is bytes for v in prefixes)
 checks.append(dict(borrowed=borrowed,samples=len(prefixes),unique_prefixes=len(set(prefixes)),logical_prefix_bytes=sum(map(len,prefixes)),unique_prefix_bytes=sum(map(len,set(prefixes)))))
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/source-prefix-reuse-20261007');cp.mkdir(exist_ok=True)
(cp/'result.json').write_text(json.dumps(dict(result='PASS',checks=checks,scope='Eight actual captured samples after owner close; exact encode payload/byte accounting versus baseline, only immutable prefixes shared; no live cadence proof.'),indent=2))
for name in ('test_source_prefix_reuse.py','owned_source_process_service_candidate.py','owned_source_process_service_candidate.py.before-prefix-reuse'):(cp/name).write_bytes(Path('work/camera',name).read_bytes())
print(checks)