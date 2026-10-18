"""Summarize exact original-cell coverage holes; does not change clipping."""
import json
from pathlib import Path
folder=Path(r'C:\NFSUG-Workspace\NFSUG-android-local\app-background-scene-gpu-tests')
r=json.loads((folder/'background-scene-gpu-android-report.json').read_text())
summary=[]
for d in r['coverage_details']:
 points={tuple(p) for p in d['coordinates']}
 expected={(x,y) for y in range(107,160) for x in (238,239)}
 summary.append(dict(kind=d['kind'],refresh=d['refresh'],holes=d['holes'],exact_right_strip=points==expected))
report=dict(result='COVERAGE_GAPS_LOCALIZED',details=summary,repeat_identical=r['coverage_details'][0]==r['coverage_details'][2],apk_sha256=r['apk_sha256'])
assert all(d['exact_right_strip'] and d['holes']==106 for d in summary)
(folder/'coverage-strip-report.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report))
