from pathlib import Path
from types import SimpleNamespace
from concurrent.futures import CancelledError
import json
import owned_progressive_retirement_install_candidate as m
def retired(*args):raise CancelledError('Injected retired pair')
m.owned_draw=retired
calls=[]
def make(result):
 def check(owner,epoch,generation,probe,ctx):calls.append((owner,epoch,generation));return result
 return SimpleNamespace(owner=123,d=SimpleNamespace(nf_owned_handoff_commit_token=check))
args=(None,None,None,7,10,2,0,0,None)
assert m.draw(make(0),*args) is False
try:m.draw(make(1),*args)
except CancelledError:pass
else:raise AssertionError('Valid generation failure hidden')
try:m.draw(make(-1),*args)
except ValueError:pass
else:raise AssertionError('Invalid authority result accepted')
assert calls==[(123,2,7)]*3
out=dict(result='PASS_PROGRESSIVE_RETIREMENT_AUTHORITY',retired_native_generation_returns_false=True,valid_generation_error_propagates=True,invalid_authority_rejected=True,scope='Injected authority routing; actual live pause separate, not forced native DLL race proof.')
Path('outputs/nfsug-native-renderer/camera-research/progressive-retirement-authority-20261009.json').write_text(json.dumps(out,indent=2));print(out['result'])
