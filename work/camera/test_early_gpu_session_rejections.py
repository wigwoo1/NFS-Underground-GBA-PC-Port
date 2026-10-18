"""Reject contradictory early GPU records in isolated session copies."""
from pathlib import Path
import json,csv,re,subprocess,sys,uuid
source=Path(sys.argv[1]).resolve();session=json.loads(source.read_text(encoding='utf-8-sig'));p=Path(__file__).resolve().parent
prefix=source.parent/('gpu-negative-'+uuid.uuid4().hex);out=p/'early-gpu-session-rejection-tests.json';out.write_text(json.dumps(dict(result='RUNNING')));records=[]
try:
 for case in ('missing-gpu-column','wrong-gpu-lifetime','wrong-gpu-increment','failed-image-check','invalid-reuse-flag'):
  candidate=dict(session);manifest=Path(str(prefix)+'-'+case+'.json');log=Path(session['log']).read_text();rows=list(csv.DictReader(Path(session['display_trace']).open()))
  if case=='missing-gpu-column':
   for row in rows:del row['early_gpu_total_ns']
  elif case=='wrong-gpu-lifetime':log=re.sub(r'\bearly_gpu_discarded=(\d+)',lambda match:'early_gpu_discarded='+str(int(match[1])+1),log)
  elif case=='wrong-gpu-increment':rows[1]['early_gpu_since_display_ns']=str(int(rows[1]['early_gpu_since_display_ns'])+1)
  elif case=='failed-image-check':log=re.sub(r'\bearly_gpu_verify_failed=\d+','early_gpu_verify_failed=1',log)
  else:next(row for row in rows if int(row['early_gpu_reused']))['early_gpu_reused']='2'
  trace=Path(str(prefix)+'-'+case+'.csv')
  with trace.open('w',newline='') as stream:
   writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
  logpath=Path(str(prefix)+'-'+case+'.log');logpath.write_text(log);candidate.update(display_trace=str(trace),log=str(logpath));manifest.write_text(json.dumps(candidate))
  run=subprocess.run([sys.executable,str(p/'verify_prototype_session.py'),str(manifest)],text=True,capture_output=True)
  report=json.loads(manifest.with_name(manifest.stem+'-verification.json').read_text());assert run.returncode!=0 and report['result']=='FAIL',case
  records.append(dict(case=case,rejected=True,error=report['error']))
except Exception as error:
 out.write_text(json.dumps(dict(result='FAIL',error=str(error)),indent=2));raise
report=dict(result='PASS',records=records,scope='Copied metadata only; missing GPU fields, inconsistent render lifetime, changed timing ledger, reported image mismatch and invalid reuse flag rejected. Original session/ROM/state untouched.')
out.write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
