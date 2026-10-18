import json,struct,time,statistics
from pathlib import Path
from owned_closed_graph import ClosedGraph as Original
from owned_closed_graph_links_candidate import ClosedGraph as Candidate
raw=Path('work/camera/owned-closed-graph-last.bin').read_bytes();h=struct.unpack_from('<8I',raw);cursor=40+h[3]+h[4];end=cursor+h[5]
while cursor<end:
 oh=struct.unpack_from('<8I',raw,cursor)
 if oh[5]:break
 cursor+=128+oh[6]
assert cursor<end
ids={struct.unpack_from('<I',raw,cursor+128+i*168)[0] for i in range(oh[5])}
absent=next(i for i in range(65535) if i not in ids);first=struct.unpack_from('<I',raw,cursor+128)[0]
cases=[]
for name,offset,fmt,value in [('cycle',cursor+134,'<H',first),('missing_link',cursor+134,'<H',absent),('unreachable',cursor+16,'<I',65535),('missing_head',cursor+16,'<I',absent),('camera',cursor+32,'<B',raw[cursor+32]^1),('bad_count',cursor+24,'<I',oh[6]+1)]:
 b=bytearray(raw);struct.pack_into(fmt,b,offset,value);results=[]
 for cls in (Original,Candidate):
  try:cls.decode(b)
  except (ValueError,struct.error) as e:results.append((type(e).__name__,str(e)))
  else:results.append(('accepted',''))
 assert results[0]==results[1] and results[0][0]!='accepted',(name,results)
 cases.append(dict(case=name,error=results[0]))
rounds={'original':[],'candidate':[]}
for n in range(20):
 for name,cls in ([('original',Original),('candidate',Candidate)] if n%2==0 else [('candidate',Candidate),('original',Original)]):
  start=time.perf_counter_ns()
  for _ in range(40):cls.decode(raw)
  if n>=4:rounds[name].append((time.perf_counter_ns()-start)/40/1e6)
r=dict(result='PASS_CHAIN_REJECTION_PARITY',cases=cases,measured_rounds=16,calls_per_round=40,median_decode_ms={k:statistics.median(v) for k,v in rounds.items()},rounds=rounds,scope='One actual captured graph plus six corruptions; interleaved component wall-time measurements under uncontrolled external load. Not live/fullscene performance proof.')
Path('work/camera/closed-graph-links-boundaries.json').write_text(json.dumps(r,indent=2));print(json.dumps({k:v for k,v in r.items() if k!='rounds'},indent=2))
