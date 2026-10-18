from pathlib import Path
import ctypes as C,json,math,time
p=Path('work/camera');candidate=C.CDLL(str((p/'road-row-lattice-coverage.dll').resolve())).nf_road_row_lattice_coverage;original=C.CDLL(str((p/'road-write-ledger.dll').resolve())).nf_road_write_ledger;candidate.argtypes=original.argtypes=[C.c_void_p,C.c_uint,C.c_void_p,C.c_void_p,C.c_void_p];table=C.create_string_buffer((p/'road-correction-reciprocal.bin').read_bytes());roads=json.loads((p/'world-source-clipped-rings.json').read_text())['checks'];bounds={r['command']:(C.c_uint16*4)(*r['bounds']) for r in roads};checks=[]
def evaluate(ring,cmd):
 data=(C.c_double*(len(ring)*6))(*(v for r in ring for v in r));out=(C.c_double*(38400*3))();assert candidate(data,len(ring),bounds[cmd],table,out);return out
for road in roads:
 ring=road['clipped_ring'];out=evaluate(ring,road['command']);writes=(C.c_int16*(38400*2))();data=(C.c_double*(len(ring)*6))(*(v for r in ring for v in r));assert original(data,len(ring),bounds[road['command']],table,writes)
 for i in range(38400):assert list(out[i*3:i*3+3])==([float(writes[i*2]),float(writes[i*2+1]),1.] if writes[i*2]>=0 else [0.,0.,0.])
 checks.append(dict(command=road['command'],integer_endpoint_pairs=38400))
for fixture in json.loads((p/'world-road-ledger-axis-motion-audit.json').read_text())['checks']:
 if fixture['ledger_accepted']:continue
 ring=fixture['rejected_ring'];start=time.perf_counter();out=evaluate(ring,fixture['command']);duration=time.perf_counter()-start;assert all(math.isfinite(v) for v in out);assert all(-1e-12<=out[i*3+2]<=1+1e-12 for i in range(38400))
 # Probe limits on either side of one fractional row's nearest integer anchor.
 vertex=next(i for i,r in enumerate(ring) if r[1]!=math.floor(r[1]));lo=[r.copy() for r in ring];hi=[r.copy() for r in ring];anchor=round(ring[vertex][1]);lo[vertex][1]=anchor-1e-8;hi[vertex][1]=anchor+1e-8;a=evaluate(lo,fixture['command']);b=evaluate(hi,fixture['command']);gap=max(abs(x-y) for x,y in zip(a,b));assert gap<1e-4,gap
 checks.append(dict(command=fixture['command'],axis=fixture['world_axis'],translation=fixture['world_translation'],fractional_coverage_pixels=sum(1e-12<out[i*3+2]<1-1e-12 for i in range(38400)),two_sided_integer_row_moment_gap=gap,seconds=duration))
report=dict(result='PASS',checks=checks,scope='Experimental row-lattice coverage moments: original integer winners exact,12world fractional rings accepted,one row-coordinate seam each. X/Q quantization, full motion, texture sampling, GPU efficiency and live integration unproven.');(p/'road-row-lattice-coverage-tests.json').write_text(json.dumps(report,indent=2));print(report)
