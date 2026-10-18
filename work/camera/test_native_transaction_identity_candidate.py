import json,copy
from pathlib import Path
from owned_native_transaction_identity_candidate import validate
r=json.loads(Path('work/camera/prototype-runs/owned-native-1791566666987903000.json').read_text())
rows=[x for x in r['presentation_samples'] if x['native_result']==1]
for x in rows:validate(x)
base=rows[-1];tests=[]
def reject(name,change):
 row=copy.deepcopy(base);change(row)
 try:validate(row)
 except (ValueError,KeyError):tests.append(name)
 else:raise AssertionError(name)
reject('wrong_commit_identity',lambda r:r['commit'].__setitem__(2,0))
reject('wrong_alpha',lambda r:r.__setitem__('alpha',.123456))
reject('wrong_deadline',lambda r:r['native_transaction']['wait'].__setitem__(1,0))
reject('early_wait',lambda r:r['native_transaction']['wait'].__setitem__(2,0))
reject('double_callback',lambda r:r['native_transaction'].__setitem__('native_callback_count',2))
reject('failed_batch',lambda r:r['native_transaction'].__setitem__('native_batch_result',38))
reject('commit_before_present',lambda r:r['native_transaction']['presentation']['present_stage_ns'].__setitem__('queried',r['commit'][6]+1))
reject('future_before_native_end',lambda r:r['native_transaction']['renderer_dispatch'].__setitem__('completed_ns',0))
out=dict(result='PASS_NATIVE_TRANSACTION_IDENTITY_NEGATIVE_GUARDS',actual_rows=len(rows),rejections=tests)
Path('work/camera/prototype-runs/native-transaction-identity-guards-20261009.json').write_text(json.dumps(out,indent=2));print(out)
