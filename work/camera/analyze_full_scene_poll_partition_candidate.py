import json,sys,copy
from pathlib import Path
def analyze(r):
 assert len(r['rows'])==12 and not r['missed'] and r['pending']==0
 rows=[]
 for x in r['rows']:
  a,b,c,d=x['native_poll_profile'];begin=x['poll_begin_ns'];end=x['poll_end_ns']
  assert begin<=a<=b<=c<=d<=end
  spans=[a-begin,b-a,c-b,d-c,end-d];assert sum(spans)==end-begin
  rows.append(dict(identity=x['identity'],poll_ms=(end-begin)/1e6,python_to_map_ms=spans[0]/1e6,map_ms=spans[1]/1e6,copy_ms=spans[2]/1e6,unmap_ms=spans[3]/1e6,native_to_python_ms=spans[4]/1e6))
 return dict(result='PASS_FULL_FRAME_NATIVE_POLL_PARTITION',rows=rows,pretouch_ms=r['pretouch_ns']/1e6,max_copy_ms=max(x['copy_ms'] for x in rows),max_native_to_python_ms=max(x['native_to_python_ms'] for x in rows),scope='Exact owner-thread native map/copy/unmap/final stamps partitioned against Python call boundaries. Native-to-Python includes ctypes epilogue/GIL/scheduling; overlap/cost is not exclusive cause or scanout60 proof.')
r=json.loads(Path(sys.argv[1]).read_text());out=analyze(r);bad=copy.deepcopy(r);bad['rows'][0]['native_poll_profile'][2]=bad['rows'][0]['native_poll_profile'][1]-1
try:analyze(bad)
except AssertionError:out['reverse_native_clock_negative_control']='PASS'
else:raise AssertionError('Native reversal accepted')
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(json.dumps(out))
