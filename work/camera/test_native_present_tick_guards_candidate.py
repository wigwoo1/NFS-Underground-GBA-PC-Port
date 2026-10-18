import copy,json,subprocess,sys,tempfile
from pathlib import Path
r=json.loads(Path('work/camera/prototype-runs/owned-native-1791561577978687600.json').read_text());s=r['presentation_samples'][-1];p=s['presentation']
gap=dict(display_index=s['display_index'],interval_ns=40000000,native_present_ticks=p['native_present_ticks'],present_stage_ns=p['present_stage_ns'])
base={'bounded_diagnostic_stats':{'whole_run_api_intervals':{'long_intervals':dict(dropped=0,total=1,records=[gap])}}}
cases=[]
x=copy.deepcopy(base);x['bounded_diagnostic_stats']['whole_run_api_intervals']['long_intervals']['dropped']=1;cases.append(x)
for slot,value in [(0,0),(3,0),(5,10**18)]:
 x=copy.deepcopy(base);x['bounded_diagnostic_stats']['whole_run_api_intervals']['long_intervals']['records'][0]['native_present_ticks'][slot]=value;cases.append(x)
with tempfile.TemporaryDirectory() as folder:
 for i,x in enumerate([base]+cases):
  p=Path(folder)/'in.json';out=Path(folder)/str(i);p.write_text(json.dumps(x))
  a=subprocess.run([sys.executable,'work/camera/analyze_complete_native_present_ticks_candidate.py',str(p),str(out)],capture_output=True,text=True)
  assert (a.returncode==0)==(i==0),(i,a.stderr)
result=dict(result='PASS_NATIVE_PRESENT_TICK_GUARDS',valid=1,rejected=len(cases),scope='Actual captured native timestamps in synthetic one-record ledger; reject drops/zero frequency/reversal/outside outer phase. Not live whole-run evidence.')
Path('work/camera/prototype-runs/native-present-tick-guards-20261009.json').write_text(json.dumps(result,indent=2));print(result)
