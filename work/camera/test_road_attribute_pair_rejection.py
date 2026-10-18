"""Current renderer must reject enriched road records before drawing."""
from pathlib import Path
import struct,subprocess,json
p=Path('work/camera').resolve();cases=[]
for mode in (0,1):
 first=p/f'road-attributes-mode-{mode}.packet';raw=first.read_bytes();second=bytearray(raw);serial,begin,end=struct.unpack_from('<3I',raw,16);struct.pack_into('<3I',second,16,serial+1,end+1,end+4);later=p/f'road-attributes-mode-{mode}-next.packet';later.write_bytes(second)
 result=subprocess.run([str(p/'classified-pair-preview.exe'),str(first),str(later)],capture_output=True,text=True)
 assert result.returncode==41,(mode,result.returncode,result.stdout,result.stderr)
 # Wrapper's return99 would indicate stale borrowed arrays after rejection.
 cases.append(dict(affine=bool(mode),renderer_rejection=result.returncode))
report=dict(result='PASS',cases=cases,scope='Current rebuilt acquired-pair renderer rejects both enriched road modes before render and clears borrowed metadata. Not correction rendering or gameplay verification; explicit consumer support remains next.')
(p/'road-attribute-pair-rejection-tests.json').write_text(json.dumps(report,indent=2));print(report)
