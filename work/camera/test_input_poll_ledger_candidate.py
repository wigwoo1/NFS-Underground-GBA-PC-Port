import sys,json
from pathlib import Path
sys.path.insert(0,'work/camera')
from owned_input_poll_ledger_candidate import InputPollLedger
x=InputPollLedger(2)
small=dict(total_ns=1000,message_pump_ns=300,keyboard_ns=300,controller_ns=300,snapshot_ns=100)
slow=dict(total_ns=8646300000,message_pump_ns=8646299000,keyboard_ns=300,controller_ns=300,snapshot_ns=400)
x.observe(slow)
for _ in range(1000):x.observe(small)
assert x.rows[0]['index']==1 and x.rows[0]['total_ns']==slow['total_ns']
x.observe(slow);x.observe(slow);assert x.count==1003 and x.long_count==3 and x.dropped==1 and len(x.rows)==2
before=x.stats();bad=dict(small,total_ns=-1)
try:x.observe(bad);raise AssertionError('acceptedinvalid')
except ValueError:pass
assert x.stats()==before;x.closed=True
try:x.observe(small);raise AssertionError('acceptedclosed')
except RuntimeError:pass
Path('work/camera/prototype-runs/input-poll-ledger-component-20261010.json').write_text(json.dumps({'result':'PASS_BOUNDED_INPUT_POLL_RETENTION','polls':x.count,'retained_long':len(x.rows),'overflow':x.dropped,'scope':'Synthetic long-first/recent-window-survival/explicit overflow/invalid atomicity/closed guards; not live stall proof.'},indent=2));print('PASS_BOUNDED_INPUT_POLL_RETENTION')
