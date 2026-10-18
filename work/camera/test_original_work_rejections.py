"""Original-update accounting may not lose earlier polls or terminal work."""
from pathlib import Path
import csv,json,subprocess,sys,uuid
source=Path(sys.argv[1]).resolve();session=json.loads(source.read_text(encoding='utf-8-sig'));p=Path(__file__).resolve().parent;prefix=source.parent/('work-negative-'+uuid.uuid4().hex);out=p/'original-work-rejection-tests.json';out.write_text(json.dumps(dict(result='RUNNING')));records=[]
try:
 for case in ('missing-work-column','changed-work-increment','changed-step-increment','due-steps-exceed-total'):
  rows=list(csv.DictReader(Path(session['display_trace']).open()));candidate=dict(session)
  if case=='missing-work-column':
   for row in rows:del row['simulation_total_ns']
  elif case=='changed-work-increment':rows[1]['simulation_since_display_ns']=str(int(rows[1]['simulation_since_display_ns'])+1)
  elif case=='changed-step-increment':rows[1]['original_steps_since_display']=str(int(rows[1]['original_steps_since_display'])+1)
  else:rows[1]['display_simulation_steps']=str(int(rows[1]['original_steps_since_display'])+1)
  trace=Path(str(prefix)+'-'+case+'.csv');manifest=Path(str(prefix)+'-'+case+'.json')
  with trace.open('w',newline='') as stream:
   writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
  candidate['display_trace']=str(trace);manifest.write_text(json.dumps(candidate))
  run=subprocess.run([sys.executable,str(p/'verify_prototype_session.py'),str(manifest)],text=True,capture_output=True)
  report=json.loads(manifest.with_name(manifest.stem+'-verification.json').read_text());assert run.returncode!=0 and report['result']=='FAIL',case
  records.append(dict(case=case,rejected=True,error=report['error']))
except Exception as error:
 out.write_text(json.dumps(dict(result='FAIL',error=str(error)),indent=2));raise
report=dict(result='PASS',records=records,scope='Copied session display metadata only; missing original ledger, changed work/step increments or undercounted due steps rejected. Original recording/ROM/checkpoint untouched.')
out.write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
