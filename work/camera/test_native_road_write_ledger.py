from pathlib import Path
import ctypes as C,json,sys
p=Path('work/camera');native=C.CDLL(str((p/'road-write-ledger.dll').resolve())).nf_road_write_ledger;native.argtypes=[C.c_void_p,C.c_uint,C.c_void_p,C.c_void_p,C.c_void_p];native_checks=[]
def verify_native(road,ring,write_ledger,table):
 data=(C.c_double*(len(ring)*6))(*(v for row in ring for v in row));bounds=(C.c_uint16*4)(*road['bounds']);out=(C.c_int16*(38400*2))();assert native(data,len(ring),bounds,table,out)
 actual={i:(out[i*2],out[i*2+1]) for i in range(38400) if out[i*2]>=0};assert actual==write_ledger
 bad=list(data);bad[1]+=.25;sentinel=(C.c_int16*(38400*2))(*([77]*(38400*2)));assert not native((C.c_double*len(bad))(*bad),len(ring),bounds,table,sentinel);assert all(v==77 for v in sentinel)
 native_checks.append(dict(command=road['command'],exact_destination_source_pairs=len(actual),atomic_fractional_row_rejection=True))
s=(p/'sample_original_write_order_oracle.py').read_text();begin=s.index('# Independent diagnostic oracle.');end=s.index("for road,g in zip(r['checks'],geo['roads']):",begin);s=s[:begin]+s[end:];s=s.replace('stable-road-owned-continuous-clipped-rings.json','world-source-clipped-rings.json');s=s.replace(' fixture=(p/', ' verify_native(road,ring,write_ledger,table)\n fixture=(p/');s=s.replace('stable-road-original-write-order-oracle-','native-road-ledger-pixels-');sys.argv=['ledger','1'];exec(compile(s,'native_ledger_differential','exec'),globals());report=dict(result='PASS',checks=native_checks,scope='C endpoint coverage ledger exact against independent Python write order; fractional scan scheduler/GPU consumption pending.');(p/'native-road-write-ledger-tests.json').write_text(json.dumps(report,indent=2));print(report)
