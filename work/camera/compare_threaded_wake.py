"""Sequential AB/BA comparison; identical checkpoint/input, original-rate replay."""
from pathlib import Path
import subprocess,sys,json
p=Path(__file__).resolve().parent
out=p/'threaded-wake-comparison.json'
report=dict(result='RUNNING',seconds=15,order=['polling','wake','wake','polling'],runs=[],scope='Sequential AB/BA wall-clock comparison on identical scripted route. No image readbacks in these runs; original input/RAM/deadline/accounting checks retained. Not scanout or smooth gameplay verification.')
out.write_text(json.dumps(report,indent=2))
try:
 for index,mode in enumerate(report['order']):
  args=[sys.executable,str(p/'test_threaded_preview.py'),'15','--no-readback']
  if mode=='polling':args.append('--polling')
  subprocess.run(args,check=True,capture_output=True,text=True,timeout=50)
  run=json.loads((p/'threaded-preview-tests.json').read_text())
  assert run['result']=='PASS' and run['readbacks_disabled']
  target=p/f'threaded-comparison-{index}-attribution.json'
  subprocess.run([sys.executable,str(p/'analyze_threaded_timing.py'),run['private_prefix']+'-worker.csv',str(target)],check=True,capture_output=True,text=True,timeout=10)
  report['runs'].append(dict(mode=mode,test=run,attribution=json.loads(target.read_text())))
  out.write_text(json.dumps(report,indent=2));print(f'{index+1}/4 {mode} PASS',flush=True)
 report['result']='PASS'
except Exception as error:
 report['result']='FAIL';report['error']=str(error);raise
finally:out.write_text(json.dumps(report,indent=2))
