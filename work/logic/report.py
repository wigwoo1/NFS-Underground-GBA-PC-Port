import csv,statistics,json
from pathlib import Path
r=list(csv.DictReader(open('work/logic/interpolated.csv')))[30:];t=[float(x['seconds'])for x in r];d=[b-a for a,b in zip(t,t[1:])];n=sum(a['hash']!=b['hash']for a,b in zip(r,r[1:]));v={'new_image_fps':n/(t[-1]-t[0]),'mode60_off':all(x['mode60']=='0'for x in r),'p95_ms':sorted(d)[int(.95*len(d))]*1000};print(v);Path('work/logic/interpolation-test.json').write_text(json.dumps(v,indent=2))
