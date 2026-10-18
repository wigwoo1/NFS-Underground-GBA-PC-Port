"""Frozen witness and mutation rejection tests for observed-history-only exception."""
from pathlib import Path
import hashlib,json,struct
from background_provenance_compare import BackgroundProvenanceLedger,auxiliary
source=Path(__file__).resolve().parent;base=Path(r'C:\NFSUG-Workspace');folder=base/'NFSUG-pc-traffic-refresh-route-tests/first-source-difference';out=base/'NFSUG-pc-background-provenance-tests';out.mkdir(exist_ok=True)
a=(folder/'baseline/owner0-kind0.bin').read_bytes();b=(folder/'candidate/owner0-kind0.bin').read_bytes();owner=[2,872,15451,15455,0];old=(2,870,15443,15447,0,30223228,3,1);new=(2,871,15447,15451,1,30216932,3,1)
def ledger():
 l=BackgroundProvenanceLedger();l.old_seen[old]=3609;l.recovered[new]=3610;return l
at,_=auxiliary(a);change=ledger().compare(a,b,[owner],3615);assert change['changed_bytes']==6 and change['recovered_record_observed_at']==3610
assert ledger().compare(a,a,[owner],3615) is None
rejected=[]
def reject(name,x,y,owners=None,l=None):
 try:(l or ledger()).compare(x,y,[owner] if owners is None else owners,3615)
 except (ValueError,struct.error):rejected.append(name);return
 raise AssertionError(name)
def flip(data,index):v=bytearray(data);v[index]^=1;return bytes(v)
reject('no independent recovered observation',a,b,l=BackgroundProvenanceLedger())
reject('unknown old record',flip(a,at+104),b)
reject('unknown recovered checksum',a,flip(b,at+104))
reject('selected provenance checksum',a,flip(b,at+128+40))
reject('selected owner identity',a,flip(b,at+128+8))
reject('display row ownership',a,flip(b,at+256))
reject('auxiliary header',a,flip(b,at))
reject('source palette/layer bytes',a,flip(b,at-10))
reject('source background bytes',a,flip(b,len(b)-10))
reject('container pointer',a,flip(b,64))
reject('truncated source',a,b[:-1])
reject('two selected owners',a,b,owners=[owner,list(new[:5])])
l=ledger();l.old_seen[new]=3609;l.recovered[old]=3610;reject('history moves backwards',b,a,l=l)
l=ledger();l.observe(b,[owner],'candidate',3615);assert new not in l.new_seen and l.new_seen[tuple(auxiliary(b)[1][1])]==3615
fresh=BackgroundProvenanceLedger();fresh.observe(b,[owner],'candidate',3615,True);assert new not in fresh.recovered
report=dict(result='PASS_OBSERVED_UNSELECTED_PROVENANCE_ONLY',positive_frozen_change=change,rejections=rejected,current_unselected_record_cannot_seed_history=True,no_runtime_capture_changes=True,helper_sha256=hashlib.sha256((source/'background_provenance_compare.py').read_bytes()).hexdigest(),script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
(out/'provenance-compare-test-report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
