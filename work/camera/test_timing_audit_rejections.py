"""Check timing audit detects incorrect source ownership, not just field ranges."""
from pathlib import Path
import csv,json,subprocess,sys
p=Path('work/camera');source=p/'live-world-classified-timestamp-smoke.csv';rows=list(csv.DictReader(source.open()));i=next(i for i,r in enumerate(rows) if int(r['ready']));guards=[]
for name,key,value in [('clock','target',float(rows[i]['target'])+.125),('phase','alpha',float(rows[i]['alpha'])+.125),('source','source_older_refresh',int(rows[i]['source_older_refresh'])+1),('refresh','refresh',int(rows[i]['refresh'])+1)]:
 altered=[dict(r) for r in rows];altered[i][key]=str(value);path=p/f'timing-audit-invalid-{name}.csv'
 with path.open('w',newline='') as f:
  writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(altered)
 result=subprocess.run([sys.executable,str(p/'audit_presentation_startup.py'),path.name],capture_output=True,text=True);assert result.returncode!=0 and 'AssertionError' in result.stderr,(name,result.stdout,result.stderr);guards.append(name)
report=dict(result='PASS',rejected_corruptions=guards,scope='Recorded audit rejects perturbed original-clock target, alpha, source scene timestamp and simulation refresh ownership. No rendering/scanout evidence.')
(p/'timing-audit-negative-tests.json').write_text(json.dumps(report,indent=2));print(report)
