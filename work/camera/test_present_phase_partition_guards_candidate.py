import copy,json,subprocess,sys,tempfile
from pathlib import Path
r=json.loads(Path('work/camera/prototype-runs/present-phase-component-input-20261009.json').read_text())
cases=[]
x=copy.deepcopy(r);x['bounded_diagnostic_stats']['whole_run_api_intervals']['long_intervals']['dropped']=1;cases.append(x)
x=copy.deepcopy(r);x['bounded_diagnostic_stats']['whole_run_api_intervals']['long_intervals']['records'][0]['present_stage_ns']['pumped']=0;cases.append(x)
x=copy.deepcopy(r);x['bounded_diagnostic_stats']['whole_run_api_intervals']['long_intervals']['records'][0]['present_renderer_dispatch']['kind']='prepare';cases.append(x)
x=copy.deepcopy(r);del x['bounded_diagnostic_stats']['whole_run_api_intervals']['long_intervals']['records'][0]['present_stage_ns'];cases.append(x)
with tempfile.TemporaryDirectory() as folder:
 for i,x in enumerate(cases):
  p=Path(folder)/'input.json';p.write_text(json.dumps(x));output=Path(folder)/'output.json'
  result=subprocess.run([sys.executable,'work/camera/analyze_complete_present_phases_candidate.py',str(p),str(output)],capture_output=True,text=True)
  assert result.returncode!=0 and not output.exists(),i
out=dict(result='PASS_PRESENT_PHASE_REJECTION_GUARDS',cases=len(cases),scope='Rejects dropped ledger, reversed chronology, wrong dispatch kind and missing evidence.')
Path('work/camera/prototype-runs/present-phase-guards-20261009.json').write_text(json.dumps(out,indent=2));print(out)
