from pathlib import Path
import ctypes as C,json,random,time
p=Path('work/camera');dll=C.CDLL(str((p/'road-pair-uv-continuous.dll').resolve()));optimized=dll.nf_road_pair_uv_continuous;reference=dll.nf_road_pair_uv_continuous_reference
for fn in [optimized,reference]:fn.argtypes=[C.c_void_p,C.c_void_p,C.c_double,C.c_double,C.c_void_p,C.c_void_p]
table=C.create_string_buffer((p/'road-correction-reciprocal.bin').read_bytes());rng=random.Random(492);cases=[]
for i in range(1000):
 values=[rng.randrange(100000,200000),rng.randrange(200000,300000),rng.randrange(40000,60000),rng.randrange(100000,200000),rng.randrange(200000,300000),rng.randrange(40000,60000),rng.randrange(33,100),rng.randrange(0,30)]
 for j in range(8):
  if rng.randrange(2):values[j]+=rng.random()
 a=(C.c_double*3)(*values[:3]);b=(C.c_double*3)(*values[3:6]);x=(C.c_double*2)(77,88);y=(C.c_double*2)(77,88);args=(a,b,values[6],values[7],table);assert optimized(*args,x)==reference(*args,y);assert bytes(x)==bytes(y);cases.append(args)
timings={}
for label,fn in [('reference',reference),('optimized',optimized)]:
 a=(C.c_double*3)(100000,200000,60000);b=(C.c_double*3)(150000,250000,50000);out=(C.c_double*2)();begin=time.perf_counter()
 for i in range(10000):assert fn(a,b,64,20,table,out)
 timings[label]=time.perf_counter()-begin
report=dict(result='PASS',bit_exact_random_cases=1000,integer_call_seconds_10000=timings,scope='CPU corner enumeration optimization; ctypes overhead included, not gameplay/render throughput.');(p/'road-pair-uv-optimization-tests.json').write_text(json.dumps(report,indent=2));print(report)
